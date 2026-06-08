"""
Uctan-uca inference servisi — Boyutsal Spektrum Mimarisi.

Eski mimari: argmax ile tek etiket secilir, diger siniflar cople atilir.
Yeni mimari: kalibrasyon uygulanan softmax dagilimi (spektrum) hem pipeline
ciktisina hem LLM prompt'una tasınır; belirsiz cizimler icin susma mantigi
devreye girer.
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
from src.inference.calibration import TemperatureScaler


CLASSES = ["Happy", "Sad", "Angry", "Fear"]

# Herhangi bir sinifin kalibrasyon sonrasi olasılığı bu esigi gecemezse
# sistem "belirsiz" modu devreye girer ve LLM çagrilmaz.
CONFIDENCE_THRESHOLD = 0.40


class InferencePipeline:
    def __init__(
        self,
        checkpoint_path: str | Path,
        device: str = "cpu",
        enable_llm: bool = True,
        calibration_path: Optional[str | Path] = None,
    ) -> None:
        self.device = device
        self.checkpoint_path = Path(checkpoint_path)

        state = torch.load(self.checkpoint_path, map_location=device, weights_only=False)

        # Checkpoint'ten backbone ve image_only flag'ini çıkar; yoksa varsayılanlara dön
        backbone = state.get("backbone", state.get("config", {}).get("backbone", "resnet50"))
        image_only = state.get("image_only", state.get("config", {}).get("image_only", False))

        from src.models.flexible_classifier import FlexibleFusionClassifier
        self.model = FlexibleFusionClassifier(
            backbone=backbone,
            num_classes=4,
            pretrained=False,
            image_only=image_only,
        ).to(device)
        self.model.load_state_dict(state["model_state"])
        self.model.eval()

        _, self.val_transform = get_image_transforms(image_size=224)
        self.gradcam = GradCAM(self.model)
        self.llm = LLMExplainer() if enable_llm else None

        # Kalibrasyon — opsiyonel, validation set uzerinde fit edilmis olmali
        self.calibrator: Optional[TemperatureScaler] = None
        if calibration_path is not None:
            cal_path = Path(calibration_path)
            if cal_path.exists():
                self.calibrator = TemperatureScaler.load(cal_path)

    def predict(self, image_pil: Image.Image, lang: str = "tr") -> dict:
        rgb = image_pil.convert("RGB")
        clin_arr, valid_arr = extract_clinical_features(rgb)

        image_tensor = self.val_transform(rgb).unsqueeze(0).to(self.device)
        clinical_tensor = torch.from_numpy(clin_arr).unsqueeze(0).to(self.device)
        validity_tensor = torch.from_numpy(valid_arr).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(image_tensor, clinical_tensor, validity_tensor)
            logits_np = logits[0].cpu().numpy()

        # Kalibrasyon: eger Temperature Scaler yuklendiyse kullan,
        # yoksa ham softmax — ikisi de gecerli ama kalibrasyon tercih edilmeli.
        if self.calibrator is not None:
            probs = self.calibrator.calibrate(logits_np)
            is_calibrated = True
        else:
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()
            is_calibrated = False

        # Spektrum: buyukten kucuge siralanmis tam dagilim
        sorted_idx = np.argsort(probs)[::-1]
        spectrum_top2: list[tuple[str, float]] = [
            (CLASSES[i], float(probs[i])) for i in sorted_idx[:2]
        ]

        pred_idx = int(sorted_idx[0])
        pred_label = CLASSES[pred_idx]
        max_conf = float(probs[pred_idx])

        # Susma mantigi: en yuksek olasilik esigi gecemezse belirsiz mod
        low_confidence = max_conf < CONFIDENCE_THRESHOLD

        # Grad-CAM: argmax sinifi icin (belirsiz modda da hesaplanir)
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

        # Orijinal gorsel base64 (LLM vision icin)
        original_b64 = pil_to_base64_png(rgb)

        # Aciklama uretimi — yeni spektrum parametreleri ile
        explainer_kwargs = dict(
            predicted_label=pred_label,
            probs=probs_dict,
            clinical_features={k: (v if v is not None else 0.0) for k, v in clinical_features.items()},
            clinical_validity=clinical_validity,
            gradcam_summary=cam_region,
            lang=lang,
            spectrum_top2=spectrum_top2,
            is_calibrated=is_calibrated,
            low_confidence=low_confidence,
            image_b64=original_b64,
        )

        explanation: Optional[str]
        if self.llm is not None:
            explanation = self.llm.explain(**explainer_kwargs)
        else:
            from src.explain.rule_based_explainer import explain_rule_based
            explanation = explain_rule_based(**explainer_kwargs)

        # Frontend ApiResult ile uyumlu cevap + yeni spektrum alanlari
        return {
            "pred_emotion": pred_label if not low_confidence else ("Belirsiz" if lang == "tr" else "Uncertain"),
            "pred_gender": "",
            "confidence_emotion": max_conf,
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
            # --- Yeni spektrum alanlari ---
            "spectrum_top2": spectrum_top2,
            "is_calibrated": is_calibrated,
            "low_confidence": low_confidence,
        }
