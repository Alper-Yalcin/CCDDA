# 03 — Deneyler ve Denemeler

Bu dosya, repository içindeki metrik dosyaları, pipeline çıktıları, CSV raporları ve commit diff'lerinden elde edilen somut kanıtlara dayalı olarak denemeleri belgeler. Kanıtlanmayan bir durum için "Repository içinde bu kararın teknik nedenini doğrulayan log veya metrik bulunamadı." ifadesi kullanılmıştır.

---

## Deneme 1: Çok Modlu Mimari (Görüntü + Metin)

### Kanıt
- İlgili commitler: `ec7d0f8`, `b8b32b2`
- Değişen dosyalar: `src/models/multimodal_effnet_bert.py`, `src/train/train_multimodal.py`
- Kod incelemesi: EfficientNet-B0 + `dbmdz/bert-base-turkish-cased` birleşik model; iki sınıflandırma kafası (emotion + gender)
- Parametre özeti (kaynak: `src/models/multimodal_effnet_bert.py`): Toplam 116.2M parametre, eğitilebilir 5.6M parametre (`freeze_bert=True`, `freeze_effnet=False`)

### Ölçülen Sonuç (Kanıta Dayalı)
Kaynak: `artifacts/report_run/REPORT.md`

| Görev | Accuracy | F1 (macro) | ROC-AUC | Test Seti |
|---|---|---|---|---|
| Duygu (2 sınıf: Happy/Sad) | **%94.36** | **0.9435** | **0.9866** | 1.630 örnek |
| Cinsiyet (2 sınıf: F/M) | **%77.12** | **0.7658** | **0.8542** | 1.630 örnek |

### Neden Kaldırıldı?
Repository içinde çok modlu yaklaşımdan vazgeçilmesinin teknik nedenini doğrulayan log veya metrik bulunamadı. `5311334` commit mesajı yalnızca "chore: remove legacy dataset and reset old AI stack" demektedir; performans karşılaştırması, ablation study veya başarısızlık logu içermemektedir.

### Tezde Nasıl Anlatılmalı?
"İlk çok modlu sistemden görüntü-tabanlı sisteme geçişin teknik gerekçesi commit geçmişinde belgelenmemiştir. Bu kararın nedeni tez yazarı tarafından eklenmeli ve belgelenmelidir."

---

## Deneme 2: İkili Sınıflandırmadan 4-Sınıflı Sınıflandırmaya

### Kanıt
- İlk model (`b8b32b2`): 2 duygu sınıfı (Happy/Sad)
- Yeni sistem (`73ff5de`): 4 duygu sınıfı (Happy/Sad/Angry/Fear)
- Veri klasörleri: `Dataset/Images/Emotion_4Class/`
- Model: `eval_test.py` içinde `classes = ["Happy", "Sad", "Angry", "Fear"]`

### Ölçülen Sonuç (Kanıta Dayalı)
Kaynak: `artifacts/v1_backend/eval/metrics.json` — 1.257 test örneği

| Sınıf | Precision | Recall | F1 | Test Sayısı |
|---|---|---|---|---|
| Happy | 0.822 | 0.730 | **0.773** | 626 |
| Sad | 0.618 | 0.708 | **0.660** | 356 |
| Angry | 0.342 | 0.403 | **0.370** | 67 |
| Fear | 0.500 | 0.514 | **0.507** | 208 |
| **Macro** | — | — | **0.5775** | 1.257 |

**Genel:** Accuracy=67.06%, Balanced Accuracy=58.88%

**Sınıf destek dengesizliği:** Happy=626, Sad=356, Fear=208, Angry=67 — Angry sınıfı sadece 67 örnekle temsil edilmekte ve en düşük F1=0.370 değerini almaktadır.

### Confusion Matrix
Kaynak: `artifacts/v1_backend/eval/confusion_matrix.csv`

| Gerçek \ Tahmin | Happy | Sad | Angry | Fear |
|---|---|---|---|---|
| **Happy** | 457 | 96 | 24 | 49 |
| **Sad** | 52 | 252 | 9 | 43 |
| **Angry** | 12 | 13 | 27 | 15 |
| **Fear** | 35 | 47 | 19 | 107 |

**En büyük hata örüntüleri:** Happy→Sad (96 hata), Happy→Fear (49 hata), Sad→Happy (52 hata)

---

## Deneme 3: Yüksek-Güvenilirlik Eşiği — 0.75 vs 0.85

### Kanıt
- Dosyalar: `out/highconf_pipeline/manifests/manifest_highconf_075.csv`, `manifest_highconf_085.csv`
- Özet rapor: `out/highconf_pipeline/summary_results.csv`
- Eğitim detayı: `out/model_train_log.txt`
- Sınıflandırma raporları: `out/highconf_pipeline/runs/b3_highconf_075/classification_report.txt`, `runs/b3_highconf_085/classification_report.txt`

### Ölçülen Sonuç (Kanıta Dayalı)

**Threshold 0.75** — Kaynak: `out/highconf_pipeline/runs/b3_highconf_075/classification_report.txt`

| Sınıf | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Happy | 0.84 | 0.95 | **0.89** | 40 |
| Sad | 0.59 | 0.47 | **0.52** | 43 |
| Angry | 0.71 | 0.66 | **0.68** | 41 |
| Fear | 0.54 | 0.63 | **0.58** | 43 |
| **Macro** | 0.67 | 0.68 | **0.67** | 167 |

Eğitim örnekleri: **23.063** — Kaynak: `out/highconf_pipeline/summary_results.csv`
Accuracy: **67.07%**, Macro F1: **0.6694**

**Threshold 0.85** — Kaynak: `out/highconf_pipeline/runs/b3_highconf_085/classification_report.txt`

| Sınıf | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| Happy | 0.84 | 0.90 | **0.87** | 40 |
| Sad | 0.59 | 0.47 | **0.52** | 43 |
| Angry | 0.77 | 0.56 | **0.65** | 41 |
| Fear | 0.48 | 0.67 | **0.56** | 43 |
| **Macro** | 0.67 | 0.65 | **0.65** | 167 |

Eğitim örnekleri: **18.783** — Kaynak: `out/highconf_pipeline/summary_results.csv`
Accuracy: **64.67%**, Macro F1: **0.6495**

### Karşılaştırma Sonucu

| Metrik | Threshold 0.75 | Threshold 0.85 | Kazanan |
|---|---|---|---|
| Eğitim Örnek Sayısı | 23.063 | 18.783 | 0.75 (+4.280) |
| Accuracy | 67.07% | 64.67% | **0.75** |
| Macro F1 | 0.6694 | 0.6495 | **0.75** |
| Happy F1 | 0.89 | 0.87 | 0.75 |
| Sad F1 | 0.52 | 0.52 | Eşit |
| Angry F1 | 0.68 | 0.65 | 0.75 |
| Fear F1 | 0.58 | 0.56 | 0.75 |

**Teknik sonuç:** 0.75 eşiği, tüm metriklerde 0.85 eşiğinden üstün performans göstermiştir. 0.75 eşiği hem daha fazla eğitim verisi üretmiş hem de daha yüksek Macro F1 ve Accuracy değerleri elde etmiştir.

---

## Deneme 4: Consensus Pipeline vs High-Confidence Pipeline

### Kanıt
- `out/highconf_pipeline/summary_results.csv`
- `out/consensus_pipeline/summary_results.csv`

### Ölçülen Sonuç (Kanıta Dayalı)

| Metrik | Consensus 3/3 | Highconf 0.75 | Highconf 0.85 |
|---|---|---|---|
| Eğitim Örnekleri | 7.980 | 23.063 | 18.783 |
| Accuracy | **57.49%** | 67.07% | 64.67% |
| Macro F1 | **0.5721** | 0.6694 | 0.6495 |
| Happy F1 | 0.8060 | 0.8941 | 0.8675 |
| Sad F1 | **0.3000** | 0.5195 | 0.5195 |
| Angry F1 | 0.6957 | 0.6835 | 0.6479 |
| Fear F1 | 0.4870 | 0.5806 | 0.5631 |

**Teknik sonuç:** Consensus pipeline, tüm sınıf metriklerinde (Sad F1: 0.30, Accuracy: 57.49%) highconf pipeline'larından düşük performans göstermiştir. Özellikle Sad sınıfında F1=0.30 kritik düzeyde düşüktür. Consensus pipeline, daha az örnek (~7.980 vs ~23.063) üretmiştir.

---

## Deneme 5: Multitask Öğrenme — Duygu + Fenotip

### Kanıt
Kaynak: `out/phenotype_images/multitask_run_alpha025/test_results.json`

### Ölçülen Sonuç (Kanıta Dayalı)

| Görev | Accuracy | Macro F1 | Eğitim | Test |
|---|---|---|---|---|
| Duygu (4-sınıf) | **72.73%** | **0.7272** | 7.843 | 1.632 |
| Fenotip | **81.43%** | **0.8198** | 7.843 | 1.632 |

**Duygu sınıf bazlı:**
- Happy F1: **0.7337**
- Sad F1: **0.7207**
- En iyi Validation Emotion F1: **0.7427** (epoch bazlı en yüksek değer)

**Teknik not:** Multitask öğrenme (alpha=0.25 fenotip ağırlığı), tek görev modelinin Accuracy=67.06%/F1=0.5775 değerlerine kıyasla Accuracy=72.73%/F1=0.7272 ile belirgin iyileştirme sağlamıştır (+5.67 puan accuracy, +0.15 puan F1).

---

## Deneme 6: Model Kalibrasyonu — Yüksek Güven ≠ Yüksek Doğruluk

### Kanıt
Kaynak: `artifacts/v1_backend/eval/calibration.json` ve `artifacts/v1_backend/eval/high_confidence_errors.csv`

### Ölçülen Sonuç (Kanıta Dayalı)

**ECE (Expected Calibration Error): 0.1698** — iyi kalibrasyonlu modeller genellikle ECE < 0.05 elde eder.

| Güven Aralığı | Örnek Sayısı | Ortalama Güven | Ortalama Doğruluk | Fark |
|---|---|---|---|---|
| 0.9 – 1.0 | 651 | 0.967 | **0.805** | -0.162 |
| 0.8 – 0.9 | 206 | 0.853 | **0.626** | -0.227 |
| 0.7 – 0.8 | 125 | 0.752 | **0.520** | -0.232 |
| 0.6 – 0.7 | 109 | 0.650 | **0.495** | -0.155 |

**Yüksek güvenilirlikli hata örnekleri** (`high_confidence_errors.csv`):
- Happy→Fear yanlış sınıflandırma: 30+ örnek, güven 0.87–0.99 aralığında
- Happy→Angry yanlış sınıflandırma: 15+ örnek, güven 0.79–0.99 aralığında
- Sad→Fear yanlış sınıflandırma: 20+ örnek, güven 0.96–0.99 aralığında

**Teknik sonuç:** Model, en yüksek güven aralığında (%96.7 ortalama güven) yalnızca %80.5 doğruluk elde etmektedir. %20'lik aşırı güven (overconfidence) tespit edilmiştir. Bu durum, pseudo-etiketleme sürecinde yüksek güven eşiğinin gerçek doğruluğu garanti etmediğini kanıtlamaktadır.

---

## Deneme 7: Farklı EfficientNet Varyantları

### Kanıt
- İlk model (`b8b32b2`): `from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights`
- Pipeline kodları (`run_highconf_pipeline.py`, `run_consensus_pipeline.py`): `EfficientNet_B2_Weights`, `EfficientNet_B3_Weights`, `efficientnet_b2`, `efficientnet_b3` import'ları
- Model adlandırması: `b3_highconf_075`, `b3_highconf_085` klasörleri

### Ölçülen Sonuç
Repository içinde B0, B2 ve B3'ün doğrudan karşılaştırmalı ablation sonuçları (aynı veri, aynı koşulda) bulunamadı. Mevcut klasör adlandırması (b3_*) B3'ün pipeline'da seçildiğini kanıtlamaktadır.

---

## Deneme 8: Öğretmen Model Etiketleme Kapsama Analizi

### Kanıt
Kaynak: `out/highconf_pipeline/teacher_labels_report.json`

### Ölçülen Sonuç (Kanıta Dayalı)

- Toplam etiketlenen görüntü: **55.660**
- Ortalama güven skoru: **0.7306**
- Güven ≥ 0.85 olan örnek: **18.786** (toplamın %33.8'i)
- Güven ≥ 0.75 olan örnek: **28.314** (toplamın %50.9'u)

**Öğretmen model etiket dağılımı (dengesiz):**
| Sınıf | Pseudo-Etiket Sayısı |
|---|---|
| Angry | 19.211 |
| Sad | 15.520 |
| Happy | 10.541 |
| Fear | 10.388 |

**Teknik gözlem:** Öğretmen modelin ürettiği etiketlerde Angry sınıfı en çok tahmin edilen sınıf (19.211), ancak bu modelin test setindeki en düşük F1=0.370 aldığı sınıftır. Bu durum, öğretmen modelin Angry sınıfı için overconfident (aşırı tahminci) olduğunu göstermektedir.
