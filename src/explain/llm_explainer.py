"""
GPT-4o Vision destekli açıklama üretici.

Görsel doğrudan LLM'e gönderilir; model çizimdeki figürleri, renkleri,
ifadeleri kendi gözlemleriyle anlatır — salt sayısal raporun ötesinde.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Optional

from src.explain.rule_based_explainer import explain_rule_based

logger = logging.getLogger(__name__)


# Tehdit/siddet temali semantik icerik. Bunlar Kizgin (Angry) ve Korku (Fear)
# siniflariyla TUTARLIDIR; ancak Mutlu/Uzgun gibi siniflarda gecmesi aciklamayi
# modelin kararindan koparir (orn. "kanli bicak" ama sonuc Mutlu). Bu nedenle
# guardrail yalnizca SONUCLA CELISTIGINDE devreye girer.
# Not: tam-kelime esleme (regex \b) ile "olumlu", "kanıt", "yaratıcı" gibi
# masum kelimelerde yanlis tetiklenme engellenir.
_THREAT_TOKENS = (
    "bıçak", "bicak", "kanlı", "kanli", "kan", "silah", "tabanca", "tüfek", "tufek",
    "ölüm", "ölü", "öldü", "şiddet", "siddet", "yara", "bomba",
    "knife", "blood", "bloody", "weapon", "gun", "death", "violence", "wound", "stab", "kill",
)
_THREAT_RE = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _THREAT_TOKENS) + r")\b",
    re.IGNORECASE | re.UNICODE,
)
# Tehdit/siddet icerigi bu siniflarla tutarlidir; burada engellenmez.
_THREAT_CONSISTENT_LABELS = {"angry", "fear"}


def _violates_constraints(text: str, predicted_label: str) -> bool:
    """Cikti, baskin orunturyle CELISEN tehdit/siddet icerigi tasiyorsa True.

    Kizgin/Korku sonuclarinda tehdit unsurlarindan bahsetmek tutarlidir; izin verilir.
    Mutlu/Uzgun gibi sonuclarda ise bu icerik celiski yaratir -> reddedilir.
    """
    if (predicted_label or "").strip().lower() in _THREAT_CONSISTENT_LABELS:
        return False
    return _THREAT_RE.search(text) is not None


SYSTEM_PROMPT_TR = """Sen, çocukların el çizimlerini değerlendiren, psikoloji ve gelişim literatürüne hakim bir uzman asistansın.

GÖREV: Çizimde gözlemlediğin unsurları (figürler, nesneler, ifadeler, renkler, kompozisyon) sana verilen klinik göstergeler (decisive_indicators) ve benzerlik skorlarıyla birleştirerek 3-4 cümlelik doğal, akıcı Türkçe bir açıklama yaz.

TEMEL KURAL — hiçbir zaman ihlal etme:
Sistem bir çocuğun duygusunu ölçmüyor; çizimin görsel örüntülerinin eğitim veri setindeki duygu kümeleriyle ne kadar benzediğini raporluyor. Tanı koyma, sadece gözlem ve olası ilişki kur.

KRİTİK KISITLAR — kesinlikle uy:
- Açıklaman DAİMA primary_pattern (baskın örüntü) ile TUTARLI olmalı. Çizimdeki nesneleri/sembolleri betimleyebilirsin; ancak betimlemen baskın örüntüyü DESTEKLEMELİ, onunla ÇELİŞMEMELİ.
- Baskın örüntüyle çelişen içeriği öne çıkarma: sonuç Mutlu ise tehdit/şiddet/korku temalı öğeleri vurgulama. Buna karşılık sonuç Kızgın veya Korku ise, bu temalarla tutarlı gözlemleri (sert/keskin hatlar, gergin figürler, tehdit edici unsurlar, bıçak vb.) doğal biçimde anlatabilir ve sonuçla ilişkilendirebilirsin.
- secondary_pattern benzerliği %15'in altındaysa o duyguyu (korku, üzüntü vb.) öne çıkarma, "şu duygu unsurları da var" deme.
- Gerekçeni öncelikle decisive_indicators içindeki gözlemlere dayandır.

YAZIM KURALLARI:
- Somut bir gözlemle başla: "Çizimde [gözlem] dikkat çekiyor".
- "Çocuk X duygusunu yaşıyor" deme; "bu çizim X örüntüleriyle örtüşüyor" de.
- Grad-CAM odak bölgesini yalnızca anlamlıysa bir cümleyle belirt.
- is_calibrated=false ise son cümlede kısaca "olasılık oranları kalibre edilmemiştir" de.
- En sonda mutlaka: "Bu çıktı klinik tanı niteliği taşımaz; uzman değerlendirmesini destekler."
- Toplam 4 cümleyi geçme. Listeleme yapma. Doğal paragraf yaz."""

SYSTEM_PROMPT_EN = """You are an expert assistant specialising in child drawing analysis with a background in developmental psychology.

TASK: Combine what you observe in the drawing (figures, objects, expressions, colors, composition) with the clinical indicators (decisive_indicators) and similarity scores provided to you, and write a 3-4 sentence natural, flowing English explanation.

CORE RULE — never violate:
The system does NOT measure a child's emotions; it reports how closely the drawing's visual patterns resemble emotion clusters in training data. Do not diagnose — only observe and suggest possible associations.

CRITICAL CONSTRAINTS — strictly follow:
- Your explanation MUST always be CONSISTENT with primary_pattern. You may describe objects/symbols in the drawing, but the description must SUPPORT the dominant pattern, not CONTRADICT it.
- Do not foreground content that contradicts the dominant pattern: if the result is Happy, do not emphasise threat/violence/fear-themed elements. Conversely, if the result is Angry or Fear, you may naturally describe and relate observations consistent with those themes (sharp/harsh lines, tense figures, threatening elements, a knife, etc.).
- If secondary_pattern similarity is below 15%, do not foreground that emotion (fear, sadness, etc.) or say "elements of that emotion are also present".
- Ground your rationale primarily in the observations listed in decisive_indicators.

WRITING RULES:
- Start with a concrete observation: "The drawing shows [detail]…"
- Do NOT say "the child feels X"; say "this drawing overlaps with X patterns."
- Mention the Grad-CAM focus region only if meaningful.
- If is_calibrated=false, note briefly that "similarity ratios are uncalibrated."
- Always end with: "This output reflects visual pattern similarity and is not a clinical diagnosis; it should complement expert evaluation."
- Stay within 4 sentences. Write as a natural paragraph, not a list."""


class LLMExplainer:
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
        spectrum_top2: list[tuple[str, float]] | None = None,
        is_calibrated: bool = False,
        low_confidence: bool = False,
        image_b64: Optional[str] = None,
        fallback_text: Optional[str] = None,
        notable: Optional[list[dict]] = None,
    ) -> str:
        # fallback_text verilmisse (V2 gorsele-ozel narrative) basarisizlikta onu kullan;
        # yoksa eski kural-tabanli aciklayiciya don (geriye donuk uyumluluk).
        def _fallback():
            if fallback_text:
                return fallback_text
            return explain_rule_based(
                predicted_label=predicted_label,
                probs=probs,
                clinical_features=clinical_features,
                clinical_validity=clinical_validity,
                gradcam_summary=gradcam_summary,
                lang=lang,
                spectrum_top2=spectrum_top2,
                is_calibrated=is_calibrated,
                low_confidence=low_confidence,
            )

        if low_confidence or not self.is_available:
            return _fallback()

        # Sayısal bağlam — görsele ek olarak gönderilir
        sorted_probs = sorted(probs.items(), key=lambda x: x[1], reverse=True)
        # Modelin kararını yöneten gostergeler (z-skoru yuksek, gorsele ozel).
        # LLM gerekcesini BUNLARA dayandirir; ham cue'lar yerine gercek karar surucu.
        decisive_indicators = [
            {
                "indicator": n.get("indicator") or n.get("feature"),
                "observation": n.get("phrase"),
                "z": n.get("z"),
                "direction": "yuksek" if (n.get("z") or 0) > 0 else "dusuk",
            }
            for n in (notable or [])[:4]
            if n.get("phrase")
        ]
        context = {
            "primary_pattern":   {"class": sorted_probs[0][0], "similarity": round(sorted_probs[0][1], 3)},
            "secondary_pattern": {"class": sorted_probs[1][0], "similarity": round(sorted_probs[1][1], 3)} if len(sorted_probs) > 1 else None,
            "decisive_indicators": decisive_indicators,
            "is_calibrated": is_calibrated,
            "gradcam_focus": gradcam_summary or None,
            "valid_clinical_cues": {
                k: round(float(v), 3)
                for k, v in clinical_features.items()
                if int(clinical_validity.get(k, 0)) == 1
            },
        }
        context_text = json.dumps(context, ensure_ascii=False, indent=2)

        system = SYSTEM_PROMPT_EN if lang == "en" else SYSTEM_PROMPT_TR

        # Vision mesajı: görsel + sayısal bağlam
        user_content: list = []
        if image_b64:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "low"},
            })
        user_content.append({
            "type": "text",
            "text": f"Model çıktısı:\n{context_text}",
        })

        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user_content},
                ],
                temperature=0.4,
                max_tokens=350,
            )
            text = (resp.choices[0].message.content or "").strip()
            if not text:
                raise ValueError("Bos yanit")
            # Tutarlilik emniyet agi: LLM kisitlari ihlal edip semantik nesne
            # icerigi urettiyse (orn. "kanli bicak"), kararla tutarli olan
            # gosterge-tabanli narrative'e don.
            if _violates_constraints(text, predicted_label):
                logger.warning("LLM ciktisi baskin orunturle celisen tehdit icerigi tasiyor; narrative fallback kullaniliyor.")
                return _fallback()
            return text
        except Exception as exc:
            logger.warning("LLM fallback: %s", exc)
            return _fallback()
