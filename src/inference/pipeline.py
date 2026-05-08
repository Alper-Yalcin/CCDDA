"""
Uçtan-uca inference servisi.

InferencePipeline:
  - model + extractor + gradcam + llm tek seferde yuklu
  - predict(image_pil, lang) -> dict (API ile uyumlu)
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image

from src.data.transforms import get_image_transforms
from src.explain.gradcam import GradCAM, pil_to_base64_png, summarize_cam_region
from src.explain.llm_explainer import LLMExplainer
from src.features.clinical_extractor import extract_clinical_features
from src.features.feature_spec import CONFIDENCE_TIER, FEATURE_NAMES, HIGHLIGHTED_FEATURES
from src.models.fusion_classifier import ClinicalFusionClassifier


CLASSES = ["Happy", "Sad", "Angry", "Fear"]


class InferencePipeline:
    def __init__(
        self,
        checkpoint_path: str | Path,
        device: str = "cpu",
        enable_llm: bool = True,
    ) -> None:
        self.device = device
        self.checkpoint_path = Path(checkpoint_path)

        self.model = ClinicalFusionClassifier(num_classes=4, pretrained=False).to(device)
        state = torch.load(self.checkpoint_path, map_location=device)
        self.model.load_state_dict(state["model_state"])
        self.model.eval()

        _, self.val_transform = get_image_transforms(image_size=224)
        self.gradcam = GradCAM(self.model)
        self.llm = LLMExplainer() if enable_llm else None

    def predict(self, image_pil: Image.Image, lang: str = "tr") -> dict:
        rgb = image_pil.convert("RGB")
        clin_arr, valid_arr = extract_clinical_features(rgb)

        image_tensor = self.val_transform(rgb).unsqueeze(0).to(self.device)
        clinical_tensor = torch.from_numpy(clin_arr).unsqueeze(0).to(self.device)
        validity_tensor = torch.from_numpy(valid_arr).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(image_tensor, clinical_tensor, validity_tensor)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()
        pred_idx = int(np.argmax(probs))
        pred_label = CLASSES[pred_idx]

        # Grad-CAM yeni bir forward yapar (gradient gerekli) — backbone'u serbest birakir.
        try:
            cam_2d, _ = self.gradcam.compute(image_tensor, clinical_tensor, validity_tensor, target_class=pred_idx)
            overlay = self.gradcam.overlay_on_image(cam_2d, rgb)
            heatmap_b64 = pil_to_base64_png(overlay)
            cam_region = summarize_cam_region(cam_2d, lang=lang)
        except Exception:
            heatmap_b64 = None
            cam_region = ""

        clinical_features = {name: (float(clin_arr[i]) if valid_arr[i] == 1.0 else None) for i, name in enumerate(FEATURE_NAMES)}
        clinical_validity = {name: int(valid_arr[i]) for i, name in enumerate(FEATURE_NAMES)}

        probs_dict = {CLASSES[i]: float(probs[i]) for i in range(4)}

        explanation: Optional[str]
        if self.llm is not None:
            explanation = self.llm.explain(
                predicted_label=pred_label,
                probs=probs_dict,
                clinical_features={k: (v if v is not None else 0.0) for k, v in clinical_features.items()},
                clinical_validity=clinical_validity,
                gradcam_summary=cam_region,
                lang=lang,
            )
        else:
            from src.explain.rule_based_explainer import explain_rule_based
            explanation = explain_rule_based(
                predicted_label=pred_label,
                probs=probs_dict,
                clinical_features={k: (v if v is not None else 0.0) for k, v in clinical_features.items()},
                clinical_validity=clinical_validity,
                gradcam_summary=cam_region,
                lang=lang,
            )

        # Frontend ApiResult ile uyumlu cevap (gender alanlarini bos birak)
        return {
            "pred_emotion": pred_label,
            "pred_gender": "",
            "confidence_emotion": float(probs[pred_idx]),
            "confidence_gender": 0.0,
            "probs_emotion": [float(x) for x in probs.tolist()],
            "probs_gender": [],
            "class_names": list(CLASSES),
            "heatmap_emotion_b64": heatmap_b64,
            "heatmap_gender_b64": None,
            "tokens_emotion": [],
            "tokens_gender": [],
            "explanation": explanation,
            "gradcam_focus_region": cam_region,
            "clinical_features": clinical_features,
            "clinical_validity": clinical_validity,
            "feature_tiers": CONFIDENCE_TIER,
            "highlighted_features": list(HIGHLIGHTED_FEATURES),
        }
