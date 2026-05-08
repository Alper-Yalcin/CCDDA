"""
GitHub Models (OpenAI SDK uyumlu) uzerinden GPT-4o ile aciklama uretici.
GITHUB_TOKEN env yoksa veya API hata verirse rule-based fallback'e duser.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from src.explain.rule_based_explainer import explain_rule_based


logger = logging.getLogger(__name__)


SYSTEM_PROMPT_TR = """Sen, çocuk çizimlerini analiz eden açıklanabilir bir karar destek sistemi için klinik psikoloji ve bilgisayarlı görü literatürünü özümsemiş bir asistansın.

GÖREV: Verilen tahmin (Happy/Sad/Angry/Fear), olasılıklar, klinik özellik vektörü ve modelin baktığı bölge bilgisi üzerinden 3-4 cümlelik DOĞAL Türkçe açıklama üret.

KURALLAR:
- Klinik tanı KOYMA. "X duygusunu yaşıyor" gibi kesinlik kullanma. "Bu örüntü ... ile uyumlu" gibi olasılıksal dil kullan.
- Sadece validity=1 olan klinik özelliklere referans ver.
- Yorumda KLINIK LİTERATÜR DESTEĞİ olan örüntüleri vurgula:
  * Üzüntü: küçük figür, sade çizim, düşük hareket, zayıf renk
  * Öfke: koyu gölgeleme, sert açılar, koyu çizgi basıncı
  * Korku/Kaygı: parçalanma, eksiltme, küçük bağımlı figür, koyu renk
  * Mutluluk: dengeli kompozisyon, parlak renk çeşitliliği, korunmuş figür bütünlüğü
- Modelin baktığı bölgeyi (Grad-CAM özeti) kısaca belirt.
- Klinik özellikler ile model tahmini ÇELİŞİYORSA bunu açıkça belirt.
- Sonunda mutlaka şu uyarıyı ekle: "Bu çıktı klinik tanı değildir, uzman değerlendirmesini destekler."
- Cevabın 4 cümleyi geçmesin."""

SYSTEM_PROMPT_EN = """You are an explainability assistant grounded in clinical psychology and computer vision literature for child drawing analysis.

TASK: Given a prediction (Happy/Sad/Angry/Fear), probabilities, a clinical feature vector and the model's focus region, produce a 3-4 sentence natural English explanation.

RULES:
- Do NOT make clinical diagnoses. Use probabilistic language ("this pattern is consistent with...") rather than certainty.
- Only reference clinical features whose validity=1.
- Highlight literature-supported patterns:
  * Sadness: small figure, simplified, low motion, weak color
  * Anger: heavy shading, sharp angles, dark stroke pressure
  * Fear/Anxiety: fragmentation, omission, small dependent figure, dark color
  * Happiness: balanced composition, vivid color diversity, preserved figure integrity
- Briefly mention the focus region (Grad-CAM summary).
- If clinical features CONTRADICT the model prediction, state that explicitly.
- Always end with: "This output is research support, not a clinical diagnosis; it complements expert evaluation."
- Keep it within 4 sentences."""


def _build_user_payload(
    predicted_label: str,
    probs: dict[str, float],
    clinical_features: dict[str, float],
    clinical_validity: dict[str, int],
    gradcam_summary: str,
) -> str:
    valid_feats = {k: round(float(v), 4) for k, v in clinical_features.items() if int(clinical_validity.get(k, 0)) == 1}
    invalid_keys = sorted(k for k in clinical_features if int(clinical_validity.get(k, 0)) == 0)
    payload = {
        "prediction": predicted_label,
        "class_probabilities": {k: round(float(v), 4) for k, v in probs.items()},
        "valid_clinical_features": valid_feats,
        "invalid_or_missing": invalid_keys,
        "gradcam_focus_region": gradcam_summary,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


class LLMExplainer:
    """GitHub Models endpoint uzerinden chat completions."""

    DEFAULT_BASE_URL = "https://models.inference.ai.azure.com"
    DEFAULT_MODEL = "gpt-4o-mini"

    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_MODELS_TOKEN")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL", self.DEFAULT_BASE_URL)
        self.model = model or os.environ.get("LLM_MODEL", self.DEFAULT_MODEL)
        self._client = None
        if self.token:
            try:
                from openai import OpenAI
                self._client = OpenAI(base_url=self.base_url, api_key=self.token)
            except Exception as exc:
                logger.warning("OpenAI client init basarisiz: %s", exc)
                self._client = None

    @property
    def is_available(self) -> bool:
        return self._client is not None

    def explain(
        self,
        predicted_label: str,
        probs: dict[str, float],
        clinical_features: dict[str, float],
        clinical_validity: dict[str, int],
        gradcam_summary: str,
        lang: str = "tr",
    ) -> str:
        if not self.is_available:
            return explain_rule_based(predicted_label, probs, clinical_features, clinical_validity, gradcam_summary, lang)

        system = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_TR
        user = _build_user_payload(predicted_label, probs, clinical_features, clinical_validity, gradcam_summary)
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.3,
                max_tokens=400,
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                raise ValueError("LLM bos yanit donduruldu")
            return text
        except Exception as exc:
            logger.warning("LLM explainer fallback'e dustu: %s", exc)
            return explain_rule_based(predicted_label, probs, clinical_features, clinical_validity, gradcam_summary, lang)
