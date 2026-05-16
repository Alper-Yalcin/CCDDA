# 04 — Karşılaşılan Problemler ve Çözümler

Bu dosya, repository içindeki metrik dosyaları, commit diff'leri ve pipeline çıktılarından elde edilen somut kanıtlara dayalı olarak teknik problemleri belgeler. Kanıtlanmayan durumlar için "Repository içinde bu kararın teknik nedenini doğrulayan log veya metrik bulunamadı." ifadesi kullanılmıştır.

---

## Problem 1: 4-Sınıflı Modelde Overfitting

### Problem Kanıtı
Kaynak: `artifacts/v1_backend/train/train.log`

| Metrik | Değer |
|---|---|
| Final Training F1 | 0.9039 |
| Best Validation F1 | 0.6135 |
| Fark | **0.2904** |
| Validation Loss Aralığı | 1.0132 – 1.2129 (tüm epoch'lar boyunca yüksek) |
| Training Loss Seyri | 0.8939 (ep1) → 0.0671 (ep21) |

Training loss %92.5 düştüğü halde validation F1 yalnızca 0.6135'te kalmıştır.

### Uygulanan Çözüm
Sınıf ağırlıklarıyla dengeleme (`[0.512, 0.834, 4.906, 1.551]`) ve WeightedRandomSampler uygulandı.
Kaynak: `artifacts/v1_backend/train/train.log` — "Class Imbalance Weights" alanı

### Çözümün Etkisi
4-sınıf temel modelde Accuracy=67.06%, F1=0.5775 elde edildi. Multitask öğrenme (duygu + fenotip) ise overfitting'i kısmen azaltarak F1=0.7272'ye ulaştı.
Kaynak: `artifacts/v1_backend/eval/metrics.json`, `out/phenotype_images/multitask_run_alpha025/test_results.json`

---

## Problem 2: Sınıf Dengesizliği — Angry Sınıfı

### Problem Kanıtı
Kaynak: `artifacts/v1_backend/eval/metrics.json`

| Sınıf | Test Örneği | F1 |
|---|---|---|
| Happy | 626 | 0.773 |
| Sad | 356 | 0.660 |
| Fear | 208 | 0.507 |
| **Angry** | **67** | **0.370** |

Angry sınıfı, toplam test setinin yalnızca %5.3'ünü oluşturmaktadır. F1=0.370 diğer sınıfların çok altındadır.

Ayrıca `Dataset/Texts/GoldTest_Candidates_Auto4Class/class_counts.csv`:
- Happy: 5.430
- Sad: 3.720
- Angry: 1.420
- Fear: 290

Fear sınıfı 290 örnekle (Happy'nin %5.3'ü) en az temsil edilen sınıftır.

### Uygulanan Çözüm
Sınıf ağırlığı Angry için 4.906 (diğer sınıfların 3–9 katı) olarak belirlendi.
Kaynak: `artifacts/v1_backend/train/train.log` — "Class Imbalance Weights: [0.512, 0.834, 4.906, 1.551]"

### Çözümün Etkisi
Ağırlıklandırmaya rağmen Angry F1=0.370 olarak kalmaktadır. Bu değer, 67 test örneğiyle 27 doğru tahmin anlamına gelmektedir.
Kaynak: `artifacts/v1_backend/eval/confusion_matrix.csv`

---

## Problem 3: Model Kalibrasyonu — Yüksek Güven Yanıltıcı

### Problem Kanıtı
Kaynak: `artifacts/v1_backend/eval/calibration.json`

**ECE (Expected Calibration Error): 0.1698**

| Güven Aralığı | Ortalama Güven | Ortalama Doğruluk | Overconfidence Miktarı |
|---|---|---|---|
| 0.9 – 1.0 | 0.967 | 0.805 | **+0.162** |
| 0.8 – 0.9 | 0.853 | 0.626 | **+0.227** |
| 0.7 – 0.8 | 0.752 | 0.520 | **+0.232** |

Kaynak: `artifacts/v1_backend/eval/high_confidence_errors.csv` — Güven > 0.95 olan yanlış tahminler:
- Sad → Fear: 20+ örnek, güven 0.96–0.99
- Happy → Fear: 30+ örnek, güven 0.87–0.99

### Uygulanan Çözüm
Pseudo-etiketleme pipeline'larında 0.75 ve 0.85 güven eşikleri test edildi. Her iki eşikte de highconf verisiyle eğitim yapılarak karşılaştırmalı sonuçlar alındı.

### Çözümün Etkisi
0.75 eşiği (Accuracy=67.07%, F1=0.6694) 0.85 eşiğinden (Accuracy=64.67%, F1=0.6495) daha iyi sonuç verdi.
Kaynak: `out/highconf_pipeline/summary_results.csv`

---

## Problem 4: Consensus Pipeline'ın Düşük Sad F1'i

### Problem Kanıtı
Kaynak: `out/consensus_pipeline/summary_results.csv`

| Metrik | Consensus 3/3 | Highconf 0.75 |
|---|---|---|
| Sad F1 | **0.3000** | 0.5195 |
| Macro F1 | 0.5721 | 0.6694 |
| Accuracy | 57.49% | 67.07% |

Consensus pipeline Sad sınıfında F1=0.30 elde etmiştir; bu, random tahmin seviyesine yakın bir değerdir.

### Neden Bu Kadar Düşük?
Repository içinde consensus pipeline'ın Sad sınıfındaki başarısızlığının nedenini doğrulayan ek log veya analiz bulunamadı. Mevcut kanıt, consensus 3/3 koşulunun Sad örneklerini orantısız biçimde elediğini göstermektedir (7.980 eğitim örneği vs 23.063).

---

## Problem 5: Öğretmen Model Sınıf Bias'ı

### Problem Kanıtı
Kaynak: `out/highconf_pipeline/teacher_labels_report.json`

**Öğretmen model etiket dağılımı:**
| Sınıf | Pseudo-Etiket | Test F1 |
|---|---|---|
| Angry | **19.211** | 0.370 |
| Sad | 15.520 | 0.660 |
| Happy | 10.541 | 0.773 |
| Fear | 10.388 | 0.507 |

Öğretmen model en çok Angry etiketi üretmiştir (19.211); ancak aynı modelin test setinde Angry sınıfı F1=0.370 ile en düşük performansı göstermektedir. Bu, öğretmen modelin Angry sınıfına aşırı etiket ürettiği (overpredict) ancak gerçekte bu sınıfı iyi tanımadığı anlamına gelmektedir.

### Uygulanan Çözüm
Manifest oluşturma scriptlerinde (`build_manifest_*.py`) sınıf bazlı maksimum örnek sınırı (6.000 per class) uygulandı.
Kaynak: `out/highconf_pipeline/manifests/manifest_highconf_075_report.json`

---

## Problem 6: Metin Açıklamalarının Statik Kalması

### Problem Kanıtı
`d494e7b` commit mesajı: "Ezber cümleler ve GUI eklendi"
`src/explain/rule_based_explainer.py` dosyası commit `d494e7b`'de eklendi.

### Uygulanan Çözüm
`api_server.py` içine `GITHUB_TOKEN` ortam değişkeni ile LLM entegrasyonu eklendi. `src/explain/llm_explainer.py` dosyası yazıldı. Katmanlı fallback: LLM mevcut değilse kural tabanlı açıklama, mevcutsa dinamik açıklama.
Kaynak: `api_server.py` kaynak kodu, `1476c63` commit

---

## Problem 7: Tkinter GUI'de Uzun Açıklamaların Görüntülenememesi

### Problem Kanıtı
`339a738` commit mesajı: "Add scrollable text widget for explanation and refactor explanation generation"

### Uygulanan Çözüm
Tkinter `Text` widget'ı ile `Scrollbar` birleştirildi.
Kaynak: `339a738` commit diff

---

## Problem 8: Masaüstü Paketlemede Dosya Yolu Sorunları

### Problem Kanıtı
`2a6895c` commit'inde `src/app_paths.py` özellikle eklenmiştir. `sys.frozen` kontrolü içermektedir — bu, PyInstaller paketlenmiş ortamında dosya yollarının farklı çözümlenmesine yönelik bilinen bir geliştirme gereksinimidir.
Kaynak: `src/app_paths.py` kaynak kodu

### Uygulanan Çözüm
```python
if getattr(sys, 'frozen', False):
    # PyInstaller paketlenmiş ortam
    base = sys._MEIPASS
else:
    # Geliştirme ortamı
    base = project_root
```

---

## Problem 9: Eski AI Yığınının Kaldırılması

### Problem Kanıtı
`5311334` commit mesajı: "chore: remove legacy dataset and reset old AI stack"

README içeriği (commit `5311334`): "eski multimodal AI hattı bu repodan temizlendi", "legacy AI giris noktalari bilincli olarak devre disi birakildi"

`api_server.py` içinde `/predict` endpoint'i geçici olarak `503 Service Unavailable` dönmektedir.

### Neden Kaldırıldı?
Repository içinde çok modlu yaklaşımdan vazgeçilmesinin teknik nedenini doğrulayan log veya metrik bulunamadı. Commit mesajı teknik gerekçe içermemektedir.

### Çözümün Etkisi
4-sınıflı, görüntü-only yeni sistem inşa edildi. İlk model metrikleri (2-sınıf, F1=0.9435) artık karşılaştırma noktası olarak kullanılamaz (farklı görev sayısı ve sınıf tanımı).

---

## Problem 10: Veri Kıtlığı ve Pseudo-Etiket Üretimi

### Problem Kanıtı
KIDO veri seti: 10.856 örnek
Pipeline hedef: 20.000+ örnek

Kaynak: `out/highconf_pipeline/teacher_labels_report.json` — Toplam 55.660 görüntü etiketlendi, 23.063'ü 0.75 güven eşiğini geçti.

### Uygulanan Çözüm
Üç kaynak:
1. KIDO veri seti (orijinal)
2. HuggingFace parquet veri kümesi (eklendi)
3. Roboflow Drawing Facial Emotions veri seti (eklendi)

Kaynak: `out/highconf_pipeline/manifests/manifest_highconf_075_report.json`:
- HuggingFace: 13.726 örnek
- Dataset_Images (KIDO): 8.561 örnek

### Çözümün Etkisi
23.063 pseudo-etiketli örnek ile eğitim yapılmış; temel modele (6.024 örnek) kıyasla ~4x veri artışı sağlanmıştır.
