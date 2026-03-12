from pathlib import Path
from threading import Lock

import torch
import torch.nn.functional as F
from PIL import Image
from transformers import AutoTokenizer

from src.app_paths import resolve_bert_model_path, resolve_checkpoint_path
from src.data.transforms import get_image_transforms
from src.models.multimodal_effnet_bert import MultimodalEffNetBert
from src.explain.gradcam import GradCAM
from src.explain.text_explain import BertTextExplainer

EMOTION_ID2STR = {0: "Happiness", 1: "Sadness"}
GENDER_ID2STR = {0: "Female", 1: "Male"}


class PerceptionPipeline:
    def __init__(
        self,
        checkpoint=None,
        bert_model=None,
        max_length=128,
        device="cuda",
        use_imagenet_weights=False,
    ):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.checkpoint_path = str(checkpoint or resolve_checkpoint_path())
        self.bert_model = str(bert_model or resolve_bert_model_path())
        tokenizer_kwargs = {}
        if Path(self.bert_model).exists():
            tokenizer_kwargs["local_files_only"] = True

        self.tokenizer = AutoTokenizer.from_pretrained(self.bert_model, **tokenizer_kwargs)
        _, self.val_tf = get_image_transforms()

        ckpt = torch.load(self.checkpoint_path, map_location=self.device)
        freeze_bert = ckpt.get("args", {}).get("freeze_bert", True)
        freeze_effnet = ckpt.get("args", {}).get("freeze_effnet", False)

        self.model = MultimodalEffNetBert(
            bert_model_name=self.bert_model,
            freeze_bert=freeze_bert,
            freeze_effnet=freeze_effnet,
            use_imagenet_weights=use_imagenet_weights,
        ).to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

        self.gradcam = GradCAM(self.model, target_layer_name=None)
        self.text_explainer = BertTextExplainer(self.model)
        self.max_length = max_length
        self._lock = Lock()

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
        with self._lock:
            image_tensor = self._prep_image(pil_img)
            input_ids, attention_mask = self._prep_text(text)
            has_text = bool(text and text.strip())

            outputs = self.model(
                image=image_tensor,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            logits_emotion = outputs["logits_emotion"]
            logits_gender = outputs["logits_gender"]

            probs_emotion = F.softmax(logits_emotion.detach(), dim=1)[0]
            probs_gender = F.softmax(logits_gender.detach(), dim=1)[0]

            pe_idx = int(torch.argmax(probs_emotion))
            pg_idx = int(torch.argmax(probs_gender))

            pred_emotion_str = EMOTION_ID2STR[pe_idx]
            pred_gender_str = GENDER_ID2STR[pg_idx]

            heatmap_emotion_color, _ = self.gradcam.generate(
                image_tensor=image_tensor,
                class_logits=logits_emotion,
                class_index=pe_idx,
                retain_graph=True,
            )

            heatmap_gender_color, _ = self.gradcam.generate(
                image_tensor=image_tensor,
                class_logits=logits_gender,
                class_index=pg_idx,
                retain_graph=has_text,
            )

            tokens_emotion, scores_emotion, _ = None, None, None
            tokens_gender, scores_gender, _ = None, None, None

            if has_text:
                explain_results = self.text_explainer.explain_targets_from_outputs(
                    tokenizer=self.tokenizer,
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    outputs=outputs,
                    targets={"emotion": pe_idx, "gender": pg_idx},
                )
                tokens_emotion, scores_emotion, _ = explain_results["emotion"]
                tokens_gender, scores_gender, _ = explain_results["gender"]

            self.model.zero_grad()

            return {
                "pred_emotion": pred_emotion_str,
                "prob_emotion": float(probs_emotion[pe_idx].cpu()),
                "pred_gender": pred_gender_str,
                "prob_gender": float(probs_gender[pg_idx].cpu()),
                "probs_emotion": probs_emotion.detach().cpu().numpy(),
                "probs_gender": probs_gender.detach().cpu().numpy(),
                "heatmap_emotion": heatmap_emotion_color,
                "heatmap_gender": heatmap_gender_color,
                "tokens_emotion": tokens_emotion,
                "scores_emotion": scores_emotion,
                "tokens_gender": tokens_gender,
                "scores_gender": scores_gender,
            }
