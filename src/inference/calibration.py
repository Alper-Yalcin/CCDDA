"""
Temperature Scaling ile model kalibrasyon modülü.

Derin öğrenme modelleri softmax çıktılarında sistematik olarak aşırı güven
(overconfidence) gösterir. Bu modül, validation set üzerinde fit edilen tek
bir T skaleri ile logitleri yumuşatarak olasılıkları gerçek frekanslara
hizalar (Guo et al., 2017 — "On Calibration of Modern Neural Networks").

Kullanım:
    # Kalibrasyon fit etme (validation logitleri gerekli):
    scaler = TemperatureScaler()
    T = scaler.fit(val_logits, val_labels)   # val_logits: (N,4), val_labels: (N,)
    scaler.save("calibration.json")

    # Inference sırasında:
    scaler = TemperatureScaler.load("calibration.json")
    probs = scaler.calibrate(logits_1d)      # logits_1d: (4,) numpy array

UYARI: fit() her zaman validation set üzerinde çalıştırılmalıdır.
Training set üzerinde fit edilirse overfit nedeniyle T≈1.0 çıkar
ve düzeltme gerçekleşmez.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

import numpy as np


def _softmax(x: np.ndarray) -> np.ndarray:
    e = np.exp(x - np.max(x, axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


def _nll(logits: np.ndarray, labels: np.ndarray, T: float) -> float:
    """Negatif log-likelihood (cross-entropy) verilen T için."""
    scaled = logits / T
    probs = _softmax(scaled)
    n = len(labels)
    # Her örnek için doğru sınıf olasılığının log'u
    correct_probs = probs[np.arange(n), labels]
    return -np.mean(np.log(correct_probs + 1e-12))


class TemperatureScaler:
    """
    Tek parametreli post-hoc kalibrasyon: softmax(logits / T).

    T > 1 → dağılım yumuşar (overconfidence azalır)
    T < 1 → dağılım sertleşir (underconfidence azalır)
    T = 1 → değişiklik yok (varsayılan)
    """

    T_MIN = 0.05
    T_MAX = 10.0

    def __init__(self, temperature: float = 1.0) -> None:
        self.temperature = float(temperature)

    # ------------------------------------------------------------------
    # Fit
    # ------------------------------------------------------------------

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> float:
        """
        Validation set üzerinde NLL'i minimize eden T'yi bul.

        Args:
            logits: (N, num_classes) — modelin ham çıktısı (softmax öncesi)
            labels: (N,) — ground truth sınıf indeksleri

        Returns:
            Fit edilen T değeri
        """
        try:
            from scipy.optimize import minimize_scalar
        except ImportError as exc:
            raise ImportError(
                "Temperature Scaling için scipy gerekli: pip install scipy"
            ) from exc

        logits = np.asarray(logits, dtype=np.float64)
        labels = np.asarray(labels, dtype=np.int64)

        result = minimize_scalar(
            lambda T: _nll(logits, labels, T),
            bounds=(self.T_MIN, self.T_MAX),
            method="bounded",
        )
        self.temperature = float(result.x)
        return self.temperature

    # ------------------------------------------------------------------
    # Calibrate
    # ------------------------------------------------------------------

    def calibrate(self, logits: np.ndarray) -> np.ndarray:
        """
        Ham logitleri (1D veya 2D) kalibre edilmiş olasılıklara dönüştür.

        Args:
            logits: (num_classes,) veya (N, num_classes)

        Returns:
            Aynı şekilde kalibre edilmiş olasılık vektörü/matrisi
        """
        logits = np.asarray(logits, dtype=np.float64)
        return _softmax(logits / self.temperature).astype(np.float32)

    # ------------------------------------------------------------------
    # ECE (Expected Calibration Error)
    # ------------------------------------------------------------------

    def expected_calibration_error(
        self,
        logits: np.ndarray,
        labels: np.ndarray,
        n_bins: int = 10,
    ) -> float:
        """
        ECE hesapla — tez metriği olarak raporlanacak.

        Düşük ECE (~0.02–0.05) iyi kalibrasyonu gösterir.
        Yüksek ECE (>0.10) modelin güven puanlarının gerçeği
        yansıtmadığını gösterir.
        """
        probs = self.calibrate(logits)
        labels = np.asarray(labels, dtype=np.int64)
        confidences = probs.max(axis=1)
        predictions = probs.argmax(axis=1)
        accuracies = (predictions == labels).astype(np.float32)

        bins = np.linspace(0.0, 1.0, n_bins + 1)
        ece = 0.0
        n = len(labels)
        for lo, hi in zip(bins[:-1], bins[1:]):
            mask = (confidences > lo) & (confidences <= hi)
            if mask.sum() == 0:
                continue
            bin_acc = accuracies[mask].mean()
            bin_conf = confidences[mask].mean()
            ece += mask.sum() / n * abs(bin_acc - bin_conf)
        return float(ece)

    # ------------------------------------------------------------------
    # Persist
    # ------------------------------------------------------------------

    def save(self, path: Union[str, Path]) -> None:
        Path(path).write_text(
            json.dumps({"temperature": self.temperature}, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: Union[str, Path]) -> "TemperatureScaler":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(temperature=float(data["temperature"]))

    def __repr__(self) -> str:
        return f"TemperatureScaler(T={self.temperature:.4f})"
