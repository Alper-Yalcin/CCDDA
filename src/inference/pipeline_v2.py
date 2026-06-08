"""
InferencePipelineV2 — Kavram Darbogazi (Concept Bottleneck) nihai modeli icin
uctan-uca cikarim hatti.

Eski pipeline'dan farklari:
  - ConceptBottleneckClassifier yukler (model(image) -> logits + 16 kavram)
  - clinical_v2 figur-farkinda 16 gosterge + v2 standartlastirma kullanir
  - Aciklama: gosterge-tabanli klinik akil yurutme (Koppitz/Di Leo)
  - Grad-CAM CBM mimarisine uyarlanmistir

Cikti sozlugu eski pipeline ile AYNI anahtarlari tasir; frontend degismeden calisir.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

from clinical_v2.extractor_v2 import extract_v2
from clinical_v2.feature_spec_v2 import CLINICAL_MEANING, FEATURE_NAMES_V2, NUM_FEATURES_V2
from src.data.transforms import get_image_transforms
from src.explain.gradcam import pil_to_base64_png, summarize_cam_region
from src.models.concept_bottleneck_classifier import ConceptBottleneckClassifier

CLASSES = ["Happy", "Sad", "Angry", "Fear"]
TR = {"Happy": "Mutlu", "Sad": "Üzgün", "Angry": "Kızgın", "Fear": "Korku"}
CONFIDENCE_THRESHOLD = 0.40
Z_THRESHOLD = 0.7

# Her gostergenin (yuksek, dusuk) yonu icin dogal gozlem cumlesi
_OBS_TR = {
    "figure_size_ratio":      ("tuvale yayılmış geniş figür", "küçük ve geri çekilmiş figür"),
    "figure_centrality":      ("köşeye/kenara sıkışmış figür yerleşimi", "dengeli, merkezi figür yerleşimi"),
    "figure_vertical_pos":    ("sayfanın alt kısmına yerleşmiş figür", "sayfanın üst kısmına yerleşmiş figür"),
    "figure_tilt":            ("eğik figür duruşu", None),
    "stroke_darkness_mean":   ("baskılı ve koyu çizgiler", "hafif, soluk çizgiler"),
    "line_tremor":            ("titrek ve düzensiz çizgi yapısı", None),
    "pressure_variation":     ("değişken çizgi baskısı", None),
    "sharp_angle_ratio":      ("keskin ve köşeli hatlar", None),
    "shading_on_figure":      ("figür üzerinde yoğun gölgeleme", None),
    "part_fragmentation":     ("parçalı, kopuk çizgi düzeni", "bütünlüklü çizgi yapısı"),
    "component_count_norm":   ("çok sayıda ayrık parça", None),
    "fg_area_ratio":          ("sayfayı dolduran yoğun kompozisyon", "seyrek ve boş kompozisyon"),
    "empty_space_ratio":      ("geniş boş alan kullanımı", None),
    "dark_color_ratio":       ("koyu renk tonlarının baskınlığı", None),
    "color_warmth":           ("sıcak ve canlı renk kullanımı", "soğuk/soluk renk tonları"),
    "figure_integrity_proxy": ("bütünlüklü figür yapısı", "dağınık figür yapısı"),
}
# Sinifa ozel klinik iliskilendirme (yumusak dille)
_ASSOC_TR = {
    "Happy": "olumlu duygu durumu",
    "Sad":   "içe kapanma ve üzüntü örüntüleri",
    "Angry": "öfke ve gerginlik belirteçleri",
    "Fear":  "kaygı ve korku belirteçleri",
}

# UI'da one cikarilacak figur-farkinda gostergeler
HIGHLIGHTED_V2 = [
    "figure_size_ratio", "stroke_darkness_mean", "shading_on_figure",
    "line_tremor", "sharp_angle_ratio", "empty_space_ratio",
]


class _CBMGradCAM:
    """Concept Bottleneck icin Grad-CAM (model(image) cagrisiyla)."""

    def __init__(self, model: nn.Module) -> None:
        self.model = model
        self.target_layer = model.gradcam_target_layer
        self._act: Optional[torch.Tensor] = None
        self._grad: Optional[torch.Tensor] = None
        self._handles = [
            self.target_layer.register_forward_hook(lambda m, i, o: setattr(self, "_act", o.detach())),
            self.target_layer.register_full_backward_hook(lambda m, gi, go: setattr(self, "_grad", go[0].detach())),
        ]

    def compute(self, image: torch.Tensor, target_class: Optional[int] = None) -> tuple[np.ndarray, int]:
        self.model.eval()
        self.model.zero_grad(set_to_none=True)
        logits = self.model(image)
        if target_class is None:
            target_class = int(logits.argmax(1).item())
        logits[0, target_class].backward()
        if self._act is None or self._grad is None:
            raise RuntimeError("Grad-CAM hooks veri toplayamadi.")
        acts, grads = self._act[0], self._grad[0]
        weights = grads.mean(dim=(1, 2))
        cam = torch.relu((weights[:, None, None] * acts).sum(0)).cpu().numpy()
        if cam.max() > 0:
            cam = cam / cam.max()
        return cam, target_class

    def overlay(self, cam_2d: np.ndarray, pil: Image.Image, alpha: float = 0.45) -> Image.Image:
        w, h = pil.size
        cam = cv2.resize(cam_2d, (w, h))
        heat = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
        heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
        base = np.array(pil.convert("RGB"))
        blended = (heat.astype(np.float32) * alpha + base.astype(np.float32) * (1 - alpha)).clip(0, 255).astype(np.uint8)
        return Image.fromarray(blended)


class InferencePipelineV2:
    def __init__(
        self,
        checkpoint_path: str | Path,
        device: str = "cpu",
        enable_llm: bool = True,
        feature_stats_path: str | Path = "out/real/feature_stats_v2.json",
    ) -> None:
        self.device = device
        ckpt = torch.load(Path(checkpoint_path), map_location=device, weights_only=False)
        self.model = ConceptBottleneckClassifier(
            backbone=ckpt.get("backbone", "resnet50"),
            num_concepts=ckpt.get("num_concepts", NUM_FEATURES_V2),
            mode=ckpt.get("mode", "bottleneck"),
            pretrained=False,
        ).to(device)
        self.model.load_state_dict(ckpt["model_state"])
        self.model.eval()

        _, self.val_transform = get_image_transforms(image_size=224)
        self.gradcam = _CBMGradCAM(self.model)

        stats = json.load(open(feature_stats_path, encoding="utf-8"))
        self.mean = np.array([stats[n]["mean"] for n in FEATURE_NAMES_V2], dtype=np.float32)
        self.std = np.array([stats[n]["std"] for n in FEATURE_NAMES_V2], dtype=np.float32)

        self.llm = None
        if enable_llm:
            try:
                from src.explain.llm_explainer import LLMExplainer
                self.llm = LLMExplainer()
            except Exception:
                self.llm = None

    # ------------------------------------------------------------------
    def _narrative(self, pred_label, probs, pred_concepts_z, gradcam_summary="", lang="tr"):
        """Modelin TAHMIN ETTIGI gostergelerden gorsele OZEL dogal paragraf uretir."""
        # Dikkat cekici gostergeler (per-image; |z| esigi ustu)
        notable = []
        for i, name in enumerate(FEATURE_NAMES_V2):
            z = float(pred_concepts_z[i])
            if abs(z) >= Z_THRESHOLD:
                meaning = CLINICAL_MEANING.get(name, {})
                desc = meaning.get("high" if z > 0 else "low") or meaning.get("indicator", name)
                phrase = _OBS_TR.get(name, (None, None))[0 if z > 0 else 1]
                notable.append({"feature": name, "z": round(z, 2),
                                "indicator": meaning.get("indicator", ""),
                                "desc": desc, "phrase": phrase})
        notable.sort(key=lambda x: -abs(x["z"]))

        spectrum = sorted([(CLASSES[i], float(probs[i])) for i in range(4)], key=lambda x: -x[1])
        top1 = probs[CLASSES.index(pred_label)] * 100

        # 1) Sinif ortusmesi
        s = f"Bu çizim ağırlıklı olarak {TR[pred_label]} örüntüsüyle örtüşmektedir (%{top1:.0f})"
        if spectrum[1][1] > 0.15:
            s += f"; ikincil olarak {TR[spectrum[1][0]]} sinyalleri (%{spectrum[1][1]*100:.0f}) gözlenmektedir"
        s += ". "

        # 2) Gorsele ozel gozlemler (gercek gostergelerden)
        phrases = [n["phrase"] for n in notable if n["phrase"]][:3]
        if phrases:
            if len(phrases) == 1:
                obs = phrases[0]
            else:
                obs = ", ".join(phrases[:-1]) + " ve " + phrases[-1]
            s += f"Çizimde {obs} öne çıkan görsel unsurlar arasındadır"
            assoc = _ASSOC_TR.get(pred_label)
            if assoc:
                s += f"; bu nitelikler klinik literatürde {assoc} ile ilişkilendirilmektedir"
            s += ". "
        else:
            s += "Belirgin bir klinik gösterge öne çıkmamış; değerlendirme genel kompozisyona dayanmaktadır. "

        # 3) Grad-CAM odak bolgesi
        if gradcam_summary:
            s += f"Modelin dikkati çizimin {gradcam_summary} bölgesinde yoğunlaşmaktadır. "

        # 4) Feragatname
        s += "Bu çıktı görsel örüntü benzerliğini yansıtır; klinik tanı niteliği taşımaz, uzman değerlendirmesini destekler."
        return s, notable

    # ------------------------------------------------------------------
    def predict(self, image_pil: Image.Image, lang: str = "tr") -> dict:
        rgb = image_pil.convert("RGB")

        # v2 gosterge cikarimi (gercek degerler + standartlastirilmis)
        vals, valid = extract_v2(rgb)
        vals_z = np.where(valid > 0, (vals - self.mean) / self.std, 0.0).astype(np.float32)

        image_tensor = self.val_transform(rgb).unsqueeze(0).to(self.device)
        with torch.no_grad():
            logits, pred_concepts = self.model(image_tensor, return_concepts=True)
            probs = F.softmax(logits, dim=1)[0].cpu().numpy()
            pred_concepts_z = pred_concepts[0].cpu().numpy()

        sorted_idx = np.argsort(probs)[::-1]
        pred_idx = int(sorted_idx[0])
        pred_label = CLASSES[pred_idx]
        max_conf = float(probs[pred_idx])
        low_confidence = max_conf < CONFIDENCE_THRESHOLD
        spectrum_top2 = [(CLASSES[i], float(probs[i])) for i in sorted_idx[:2]]

        # Grad-CAM
        try:
            cam_2d, _ = self.gradcam.compute(image_tensor, target_class=pred_idx)
            overlay = self.gradcam.overlay(cam_2d, rgb)
            heatmap_b64 = pil_to_base64_png(overlay)
            cam_region = summarize_cam_region(cam_2d, lang=lang)
        except Exception:
            heatmap_b64, cam_region = None, ""

        # Klinik akil yurutme metni (modelin tahmin ettigi kavramlardan, gorsele ozel)
        narrative, notable = self._narrative(pred_label, probs, pred_concepts_z,
                                             gradcam_summary=cam_region, lang=lang)

        # LLM varsa zenginlestir; yoksa kural-tabanli narrative
        explanation = narrative
        if self.llm is not None and not low_confidence:
            try:
                clinical_feats = {n: (float(vals[i]) if valid[i] == 1.0 else 0.0)
                                  for i, n in enumerate(FEATURE_NAMES_V2)}
                clinical_valid = {n: int(valid[i]) for i, n in enumerate(FEATURE_NAMES_V2)}
                explanation = self.llm.explain(
                    predicted_label=pred_label,
                    probs={CLASSES[i]: float(probs[i]) for i in range(4)},
                    clinical_features=clinical_feats,
                    clinical_validity=clinical_valid,
                    gradcam_summary=cam_region,
                    lang=lang,
                    spectrum_top2=spectrum_top2,
                    is_calibrated=False,
                    low_confidence=low_confidence,
                    image_b64=pil_to_base64_png(rgb),
                    fallback_text=narrative,  # LLM basarisizsa V2 gorsele-ozel narrative
                    notable=notable,          # modelin karar surucu gostergeleri (grounding)
                ) or narrative
            except Exception:
                explanation = narrative

        clinical_features = {n: (float(vals[i]) if valid[i] == 1.0 else None)
                             for i, n in enumerate(FEATURE_NAMES_V2)}
        clinical_validity = {n: int(valid[i]) for i, n in enumerate(FEATURE_NAMES_V2)}

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
            "feature_tiers": {n: "high" for n in FEATURE_NAMES_V2},
            "highlighted_features": list(HIGHLIGHTED_V2),
            "notable_concepts": notable,
            "spectrum_top2": spectrum_top2,
            "is_calibrated": False,
            "low_confidence": low_confidence,
            "model_type": "concept_bottleneck_v2",
        }
