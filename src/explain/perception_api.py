# src/explain/perception_api.py

import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoTokenizer

from src.data.transforms import get_image_transforms
from src.models.multimodal_effnet_bert import MultimodalEffNetBert
from src.explain.gradcam import GradCAM
from src.explain.text_explain import BertTextExplainer

EMOTION_ID2STR = {0: "Happiness", 1: "Sadness"}
GENDER_ID2STR = {0: "Female", 1: "Male"}


class PerceptionPipeline:
    def __init__(
        self,
        checkpoint="checkpoints/best_multimodal.pt",
        bert_model="dbmdz/bert-base-turkish-cased",
        max_length=128,
        device="cuda",
    ):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(bert_model)
        _, self.val_tf = get_image_transforms()

        ckpt = torch.load(checkpoint, map_location=self.device)
        freeze_bert = ckpt.get("args", {}).get("freeze_bert", True)
        freeze_effnet = ckpt.get("args", {}).get("freeze_effnet", False)

        self.model = MultimodalEffNetBert(
            bert_model_name=bert_model,
            freeze_bert=freeze_bert,
            freeze_effnet=freeze_effnet,
        ).to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

        self.gradcam = GradCAM(self.model, target_layer_name=None)
        self.text_explainer = BertTextExplainer(self.model)
        self.max_length = max_length

    def _prep_image(self, pil_img: Image.Image):
        img_t = self.val_tf(pil_img).unsqueeze(0).to(self.device)
        return img_t

    def _prep_text(self, text: str | None):
        text = text or ""
        enc = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].to(self.device)
        attention_mask = enc["attention_mask"].to(self.device)
        return input_ids, attention_mask

    def run(self, pil_img: Image.Image, text: str | None = None):
        image_tensor = self._prep_image(pil_img)
        input_ids, attention_mask = self._prep_text(text)

        # ---- 1) Tahminler ----
        with torch.no_grad():
            outputs = self.model(
                image=image_tensor,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            logits_emotion = outputs["logits_emotion"]
            logits_gender = outputs["logits_gender"]

            probs_emotion = F.softmax(logits_emotion, dim=1)[0]
            probs_gender = F.softmax(logits_gender, dim=1)[0]

        pe_idx = int(torch.argmax(probs_emotion))
        pg_idx = int(torch.argmax(probs_gender))

        pred_emotion_str = EMOTION_ID2STR[pe_idx]
        pred_gender_str = GENDER_ID2STR[pg_idx]

        # ---- 2) Grad-CAM (emotion & gender) ----
        # Emotion
        outputs_em = self.model(
            image=image_tensor,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        heatmap_emotion_color, _ = self.gradcam.generate(
            image_tensor=image_tensor,
            class_logits=outputs_em["logits_emotion"],
            class_index=pe_idx,
        )

        # Gender
        outputs_gender = self.model(
            image=image_tensor,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        heatmap_gender_color, _ = self.gradcam.generate(
            image_tensor=image_tensor,
            class_logits=outputs_gender["logits_gender"],
            class_index=pg_idx,
        )

        # ---- 3) (Varsa) text token importance ----
        tokens_emotion, scores_emotion, _ = None, None, None
        tokens_gender, scores_gender, _ = None, None, None

        if text is not None and text.strip():
            tokens_emotion, scores_emotion, _ = self.text_explainer.explain(
                tokenizer=self.tokenizer,
                image_tensor=image_tensor,
                input_ids=input_ids,
                attention_mask=attention_mask,
                target="emotion",
                class_index=pe_idx,
                device=self.device,
            )
            tokens_gender, scores_gender, _ = self.text_explainer.explain(
                tokenizer=self.tokenizer,
                image_tensor=image_tensor,
                input_ids=input_ids,
                attention_mask=attention_mask,
                target="gender",
                class_index=pg_idx,
                device=self.device,
            )

        return {
            "pred_emotion": pred_emotion_str,
            "prob_emotion": float(probs_emotion[pe_idx].cpu()),
            "pred_gender": pred_gender_str,
            "prob_gender": float(probs_gender[pg_idx].cpu()),
            "heatmap_emotion": heatmap_emotion_color,  # np.array
            "heatmap_gender": heatmap_gender_color,    # np.array
            "tokens_emotion": tokens_emotion,
            "scores_emotion": scores_emotion,
            "tokens_gender": tokens_gender,
            "scores_gender": scores_gender,
        }
