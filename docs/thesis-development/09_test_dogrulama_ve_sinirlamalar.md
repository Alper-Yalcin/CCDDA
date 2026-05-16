# 09 — Test, Doğrulama ve Sınırlamalar

Bu dosya, repository içindeki metrik dosyaları, training logları, confusion matrix CSV'leri ve pipeline raporlarından elde edilen somut kanıtlara dayalı olarak test ve değerlendirme sürecini belgeler.

---

# Mevcut Test ve Değerlendirme Scriptleri

| Dosya | Amaç | İlk Görüldüğü |
|---|---|---|
| `eval_test.py` | `ClinicalFusionClassifier` ile 4-sınıf test değerlendirme | `73ff5de` |
| `eval_tta.py` | Test-Time Augmentation (TTA) ile değerlendirme | `73ff5de` |
| `src/eval/evaluate.py` | Temel değerlendirme fonksiyonları | Yeni sistem altyapısı |
| `tools/run_report.py` | Eğitim + değerlendirme + rapor otomasyonu | `bab2958` |

---

# Model 1: İlk Çok Modlu Sistem (2-Sınıflı, Şubat 2026)

Kaynak: `artifacts/report_run/REPORT.md`

## Eğitim Yapılandırması
| Parametre | Değer |
|---|---|
| Epoch | 5 |
| Batch size | 16 |
| Learning rate | 0.0001 (AdamW + Cosine warmup) |
| BERT | Frozen (freeze_bert=True) |
| EfficientNet | B0, eğitilebilir |
| Veri | KIDO `master_emotion_gender.csv` |
| Toplam örnek | 10.856 |

## Veri Bölünmesi
| Küme | Boyut |
|---|---|
| Train | 7.843 |
| Validation | 1.383 |
| Test | 1.630 (Duygu dengeli: Happy=815, Sad=815) |

## Test Sonuçları

| Görev | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | ROC-AUC |
|---|---|---|---|---|---|
| Duygu (2 sınıf) | **94.36%** | 0.9438 | 0.9436 | **0.9435** | **0.9866** |
| Cinsiyet (2 sınıf) | **77.12%** | 0.7637 | 0.7728 | **0.7658** | **0.8542** |

## Confusion Matrix — Duygu

| Gerçek \ Tahmin | Happy | Sad |
|---|---|---|
| **Happy** | 759 (93.1%) | 56 (6.9%) |
| **Sad** | 36 (4.4%) | 779 (95.6%) |

## Confusion Matrix — Cinsiyet

| Gerçek \ Tahmin | Female | Male |
|---|---|---|
| **Female** | 752 (76.5%) | 231 (23.5%) |
| **Male** | 142 (17.4%) | 505 (62.6%) |

**Not:** Cinsiyet sınıfı dengesizdir: Female=983, Male=647.

---

# Model 2: 4-Sınıflı Görüntü-Only Sistem — Temel Değerlendirme

Kaynak: `artifacts/v1_backend/eval/metrics.json`

## Eğitim Yapılandırması
| Parametre | Değer |
|---|---|
| Mimari | EfficientNet-B3 (ClinicalFusionClassifier) |
| Sınıflar | Happy, Sad, Angry, Fear (4 sınıf) |
| Sınıf Ağırlıkları | [0.512, 0.834, 4.906, 1.551] |
| Train | 6.024 |
| Validation | 1.064 |
| Best Epoch | 15/30 |
| Best Val F1 | 0.6135 |
| Final Train F1 | 0.9039 |

Kaynak: `artifacts/v1_backend/train/train.log`

**Training loss seyri:** 0.8939 (epoch 1) → 0.0671 (epoch 21) — Kaynak: `artifacts/v1_backend/train/train.log`

**Validation loss aralığı:** 1.0132 – 1.2129 (tüm epoch boyunca yüksek seyretti) — Kaynak: `artifacts/v1_backend/train/train.log`

**Yorum:** Training F1=0.9039 iken Validation F1=0.6135; aralarındaki 0.29 puanlık fark overfitting'e işaret etmektedir.

## Test Sonuçları (1.257 örnek)

| Sınıf | Precision | Recall | F1 | Test Sayısı |
|---|---|---|---|---|
| Happy | 0.822 | 0.730 | **0.773** | 626 |
| Sad | 0.618 | 0.708 | **0.660** | 356 |
| Angry | 0.342 | 0.403 | **0.370** | 67 |
| Fear | 0.500 | 0.514 | **0.507** | 208 |
| **Macro** | — | — | **0.5775** | 1.257 |

**Genel Accuracy:** 67.06%
**Balanced Accuracy:** 58.88%

## Confusion Matrix — 4-Sınıflı Model

Kaynak: `artifacts/v1_backend/eval/confusion_matrix.csv`

| Gerçek \ Tahmin | Happy | Sad | Angry | Fear |
|---|---|---|---|---|
| **Happy** | 457 | 96 | 24 | 49 |
| **Sad** | 52 | 252 | 9 | 43 |
| **Angry** | 12 | 13 | **27** | 15 |
| **Fear** | 35 | 47 | 19 | **107** |

**Toplam hata:** 329 / 1.257 (%26.2 hata oranı)

**En büyük hata örüntüleri:**
- Happy → Sad: 96 hata (Happy'nin %15.3'ü yanlış Sad tahmin edildi)
- Sad → Happy: 52 hata
- Happy → Fear: 49 hata
- Fear → Sad: 47 hata

---

# Model 3: High-Confidence Pipeline ile Eğitim

Kaynak: `out/model_train_log.txt`

| Parametre | Değer |
|---|---|
| Eğitim örneği (dengelenmiş) | 4.843 |
| Validation | 816 |
| Test | 816 |
| Best Epoch | 33/60 |
| Best Val F1 | 0.6007 |

## Test Sonuçları

| Sınıf | F1 |
|---|---|
| Happy | **0.7721** |
| Sad | **0.6569** |
| Angry | **0.5086** |
| Fear | **0.4242** |
| **Macro** | **0.5905** |

**Accuracy:** 63.97%

---

# Model 4: Multitask — Duygu + Fenotip

Kaynak: `out/phenotype_images/multitask_run_alpha025/test_results.json`

| Görev | Accuracy | Macro F1 | Test Seti |
|---|---|---|---|
| Duygu (4-sınıf) | **72.73%** | **0.7272** | 1.632 |
| Fenotip | **81.43%** | **0.8198** | 1.632 |

**Duygu sınıf bazlı:**
| Sınıf | F1 |
|---|---|
| Happy | **0.7337** |
| Sad | **0.7207** |

**En yüksek Validation Duygu F1:** 0.7427 (epoch bazlı en iyi)

**Karşılaştırma:** Multitask model (F1=0.7272), tek görev modelinden (F1=0.5775) +0.15 puan daha yüksek F1 elde etmiştir. Eğitim seti aynıdır (7.843 örnek).

---

# Pipeline Karşılaştırması

## Highconf 0.75 vs 0.85 vs Consensus

Kaynak: `out/highconf_pipeline/summary_results.csv`, `out/consensus_pipeline/summary_results.csv`, `out/highconf_pipeline/runs/b3_highconf_075/classification_report.txt`, `out/highconf_pipeline/runs/b3_highconf_085/classification_report.txt`

| Metrik | Consensus 3/3 | Highconf 0.75 | Highconf 0.85 |
|---|---|---|---|
| Eğitim Örnekleri | 7.980 | 23.063 | 18.783 |
| Accuracy | 57.49% | **67.07%** | 64.67% |
| Macro F1 | 0.5721 | **0.6694** | 0.6495 |
| Happy F1 | 0.8060 | **0.8941** | 0.8675 |
| Sad F1 | 0.3000 | **0.5195** | 0.5195 |
| Angry F1 | **0.6957** | 0.6835 | 0.6479 |
| Fear F1 | 0.4870 | **0.5806** | 0.5631 |

**Teknik sonuç:** Highconf 0.75 pipeline, 23.063 örnek üretmiş ve Macro F1=0.6694 ile tüm pipeline'lar arasında en iyi sonucu elde etmiştir. Consensus pipeline, 7.980 örnek üretmiş ve Macro F1=0.5721 ile en düşük performansı göstermiştir.

---

# Model Kalibrasyonu

Kaynak: `artifacts/v1_backend/eval/calibration.json`

**ECE (Expected Calibration Error): 0.1698**
(İyi kalibrasyonlu modeller genellikle ECE < 0.05 elde eder.)

| Güven Aralığı | Örnek Sayısı | Ortalama Güven | Ortalama Doğruluk | Overconfidence |
|---|---|---|---|---|
| 0.9 – 1.0 | 651 | 0.967 | 0.805 | **+0.162** |
| 0.8 – 0.9 | 206 | 0.853 | 0.626 | **+0.227** |
| 0.7 – 0.8 | 125 | 0.752 | 0.520 | **+0.232** |
| 0.6 – 0.7 | 109 | 0.650 | 0.495 | **+0.155** |

Kaynak: `artifacts/v1_backend/eval/high_confidence_errors.csv` — Yüksek güvenle yanlış sınıflandırılan örnekler:
- Happy→Fear: 30+ hata, güven aralığı 0.87–0.99
- Happy→Angry: 15+ hata, güven aralığı 0.79–0.99
- Sad→Fear: 20+ hata, güven aralığı 0.96–0.99

**Teknik sonuç:** Yüksek güven skoru modelin doğruluk garantisi değildir. 0.96–0.99 güven aralığında Sad→Fear yanlış tahminler gözlemlenmiştir.

---

# Pseudo-Etiketleme İstatistikleri

## Öğretmen Model Etiketleme Kapsamı
Kaynak: `out/highconf_pipeline/teacher_labels_report.json`

| Metrik | Değer |
|---|---|
| Toplam etiketlenen görüntü | 55.660 |
| Ortalama güven | 0.7306 |
| ≥ 0.85 güven (kullanılabilir) | 18.786 (%33.8) |
| ≥ 0.75 güven (kullanılabilir) | 28.314 (%50.9) |

**Öğretmen model etiket dağılımı:**
| Sınıf | Pseudo-Etiket Sayısı |
|---|---|
| Angry | 19.211 |
| Sad | 15.520 |
| Happy | 10.541 |
| Fear | 10.388 |

## Consensus Model Anlaşma İstatistikleri
Kaynak: `out/consensus_pipeline/ab_candidates_ab_agree_075_report.json`

| Metrik | Değer |
|---|---|
| Toplam aday | 55.660 |
| Teacher A & B anlaşması | 41.717 (%74.8) |
| Her ikisi ≥ 0.75 güven | 23.728 (%42.6) |

---

# Tüm Modellerin Özet Karşılaştırması

| Model | Sınıf | Accuracy | Macro F1 | Eğitim Verisi | Kaynak |
|---|---|---|---|---|---|
| Multimodal EfficientNet+BERT | 2 (Duygu) | **94.36%** | **0.9435** | 7.843 KIDO | `artifacts/report_run/REPORT.md` |
| Multimodal EfficientNet+BERT | 2 (Cinsiyet) | 77.12% | 0.7658 | 7.843 KIDO | `artifacts/report_run/REPORT.md` |
| 4-sınıf görüntü-only (temel) | 4 | 67.06% | 0.5775 | 6.024 | `artifacts/v1_backend/eval/metrics.json` |
| Highconf pipeline (0.75) | 4 | 67.07% | 0.6694 | 23.063 | `out/highconf_pipeline/summary_results.csv` |
| Highconf pipeline (0.85) | 4 | 64.67% | 0.6495 | 18.783 | `out/highconf_pipeline/summary_results.csv` |
| Consensus pipeline | 4 | 57.49% | 0.5721 | 7.980 | `out/consensus_pipeline/summary_results.csv` |
| **Multitask (duygu+fenotip)** | **4** | **72.73%** | **0.7272** | **7.843** | `out/phenotype_images/multitask_run_alpha025/test_results.json` |
| High-conf verisiyle eğitim | 4 | 63.97% | 0.5905 | 4.843 | `out/model_train_log.txt` |

**En iyi 4-sınıf sonuç:** Multitask öğrenme (Accuracy=72.73%, Macro F1=0.7272)

---

# Sınırlamalar (Kanıta Dayalı)

## 1. Sınıf Dengesizliği
Test setinde Angry=67 örnek (tüm sınıfların %5.3'ü). Angry F1=0.370, diğer sınıfların ortalama F1'inin belirgin altındadır.
Kaynak: `artifacts/v1_backend/eval/metrics.json`

## 2. Overfitting
Training F1=0.9039 vs Validation F1=0.6135 — 0.29 puanlık fark.
Kaynak: `artifacts/v1_backend/train/train.log`

## 3. Zayıf Kalibrasyon
ECE=0.1698; yüksek güven %96.7 ortalama güvende yalnızca %80.5 doğruluk sağlamaktadır.
Kaynak: `artifacts/v1_backend/eval/calibration.json`

## 4. Öğretmen Model Sınıf Bias'ı
Öğretmen model 19.211 Angry etiketi üretmiş; ancak aynı modelin test setindeki Angry F1=0.370. Öğretmen model Angry sınıfına bias'lıdır.
Kaynak: `out/highconf_pipeline/teacher_labels_report.json`

## 5. Consensus Pipeline Sad Sınıfı Zayıflığı
Consensus pipeline Sad F1=0.30; bu değer highconf 0.75 pipeline Sad F1=0.52'nin belirgin altındadır.
Kaynak: `out/consensus_pipeline/summary_results.csv`

## 6. Klinik Doğrulama Yok
Repository içinde klinisyen değerlendirmesi veya kullanıcı testi logu bulunamadı.

## 7. Pseudo-Etiket Güvenilirliği
Yüksek güven skoru gerçek doğruluğu garanti etmemektedir. ECE=0.1698 ve yüksek güvenilirlikli hata analizi bunu kanıtlamaktadır.
Kaynak: `artifacts/v1_backend/eval/calibration.json`, `artifacts/v1_backend/eval/high_confidence_errors.csv`
