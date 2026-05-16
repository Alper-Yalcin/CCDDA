# 09 — Test, Doğrulama ve Sınırlamalar

Bu dosya, projede uygulanan test ve doğrulama süreçlerini ve sistemin bilinen sınırlamalarını belgeler.

---

# Test İzleri

## Resmi Test Altyapısı

Projede ayrı bir birim test (unit test) klasörü ya da test çerçevesi (pytest, unittest vb.) görülmemektedir. Bu, formalize edilmiş otomatik test kapsaminın olmadığını göstermektedir — ancak bu tür araştırma proje geliştirmelerinde sıklıkla görülen bir durumdur.

### Mevcut Test / Değerlendirme Scriptleri

| Dosya | Amaç | İlk Görüldüğü |
|---|---|---|
| `eval_test.py` | Test seti üzerinde `best.pt` checkpoint'i ile tam model değerlendirme | `73ff5de` (Mayıs 2026) |
| `eval_tta.py` | Test-Time Augmentation (TTA) ile gelişmiş değerlendirme | `73ff5de` (Mayıs 2026) |
| `src/eval/evaluate.py` | Temel değerlendirme fonksiyonları modülü | Yeni sistem altyapısı |
| `tools/run_report.py` | Eğitim + değerlendirme + rapor üretim otomasyonu | `bab2958` (Şubat 2026) |

---

# Belgelenmiş Model Değerlendirme Sonuçları

## İlk Multimodal Model (Şubat 2026)

Kaynak: `artifacts/report_run/REPORT.md`

### Eğitim Yapılandırması
```
Epoch: 5
Batch size: 16
LR: 0.0001 (AdamW + Cosine warmup)
BERT: frozen
EfficientNet-B0: eğitilebilir
Veri: KIDO master_emotion_gender.csv
Toplam: 10.856 örnek
```

### Veri Bölünmesi
| Küme | Boyut |
|---|---|
| Train | 7.843 |
| Validation | 1.383 |
| Test | 1.630 |

Duygu sınıfları test setinde dengeli dağılmış: Happiness=815, Sadness=815.

### Test Sonuçları (Kesin)

| Görev | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | ROC-AUC |
|---|---|---|---|---|---|
| Duygu | **%94.36** | 0.9438 | 0.9436 | **0.9435** | **0.9866** |
| Cinsiyet | **%77.12** | 0.7637 | 0.7728 | **0.7658** | **0.8542** |

### Confusion Matrix — Duygu (2 sınıf)
| Gerçek \ Tahmin | Happiness | Sadness |
|---|---|---|
| Happiness | 759 (%93.1) | 56 (%6.9) |
| Sadness | 36 (%4.4) | 779 (%95.6) |

### Confusion Matrix — Cinsiyet (2 sınıf)
| Gerçek \ Tahmin | Female | Male |
|---|---|---|
| Female | 752 (%76.5) | 231 (%23.5) |
| Male | 142 (%17.4) | 505 (%62.6) |

### Önemli Yorum
Duygu sınıflandırmasında çok yüksek başarı görülmektedir (F1=0.94). Cinsiyet sınıflandırmasında performans daha düşüktür ve sınıf dengesizliği etkisi vardır (Female: 983, Male: 647). Bu sonuçlar, modelin görüntüden duygu sinyallerini cinsiyet sinyallerinden daha iyi ayırt ettiğini göstermektedir.

---

# Test-Time Augmentation (TTA)

`eval_tta.py` dosyası Test-Time Augmentation (TTA) ile değerlendirme yapmaktadır. TTA, çıkarım sırasında aynı görüntünün birden fazla augmented versiyonunu modele verip tahminleri ortalamasıyla daha sağlam sonuçlar elde eder. Bu dosyanın varlığı, standart değerlendirmenin yanı sıra daha ileri teknikler de araştırıldığını göstermektedir.

---

# Değerlendirme Scriptleri (Yeni Sistem)

`eval_test.py` dosyası yeni sistem için yazılmıştır:
- Model: `ClinicalFusionClassifier` (4 sınıf)
- Sınıflar: `["Happy", "Sad", "Angry", "Fear"]`
- Metrikler: accuracy, F1, precision, recall, confusion matrix, classification report
- Manifest: `out/manifest_qwen.csv`

Bu script muhtemelen `5311334` sıfırlamasından sonra yazılmıştır. Değerlendirme sonuçları henüz repo'da mevcut değildir (yeni model eğitimi tamamlanmamış olabilir).

---

# Pseudo-Etiket Kalite Raporları

Pseudo-etiketleme pipeline'larının çıktı raporları (`out/highconf_pipeline/`, `out/consensus_pipeline/`) bulunmaktadır.

### Highconf Pipeline Özet (`out/highconf_pipeline/summary_results.json`)
```json
(dosya mevcut ama içerik kesin tespit edilemedi — pipeline çıktısı)
```

### Consensus Pipeline Özet (`out/consensus_pipeline/summary_results.json`)
Pipeline ürettiği manifest sayıları (dosya adlarından):
- `manifest_consensus_3of3_c060.csv`: ~8.300 örnek (3/3 mutabakat + %60 güven)

---

# Manuel Doğrulama Olasılıkları

Commit geçmişinde belgelenmiş resmi bir "kullanıcı testi" ya da "klinik değerlendirme" bulunmamaktadır. Ancak şu izler manuel doğrulamaya işaret edebilir:

1. **Grad-CAM görsellerinin commit'e dahil edilmesi** (`d494e7b`): Araştırmacının model çıktılarını görsel olarak incelediğini göstermektedir.
2. **Örnek tahmin görselleri** (`artifacts/report_run/figures/sample_predictions.png`): Model çıktılarının görsel doğrulaması yapılmıştır.
3. **Web arayüzünün geliştirilmesi**: Arayüzü gerçek anlamda kullanmak için manuel test zorunludur.
4. **Run args JSON dosyası** (`run_args.json`): Hızlı tekrar çalıştırma için yapılandırma; iteratif test sürecini düşündürmektedir.

---

# Kod Üzerinden Görülen Kontroller

`run_highconf_pipeline.py` ve `run_consensus_pipeline.py` içindeki koddan anlaşılan kalite kontrol mekanizmaları:

1. **Güven eşiği filtreleri**: Yalnızca belirli güven düzeyinin üzerindeki tahminler kabul ediliyor
2. **Görüntü hash'leme**: Tekrar eden görüntüler tespit edilerek tekilleştirme yapılıyor
3. **Sınıf dağılımı kontrolü**: `Counter` kullanarak sınıf dengesizliği izleniyor
4. **Heldout test seti**: Eğitimde kullanılmayan görüntüler ayrı tutuluyor (`non-heldout` ifadesi)
5. **WeightedRandomSampler**: Sınıf dengesizliğini gidermek için ağırlıklı örnekleme

`eval_test.py` içinde şu metrikler hesaplanıyor:
- Accuracy, F1, Precision, Recall (sklearn)
- Classification report (sınıf bazlı)
- Confusion matrix

---

# Sınırlamalar

## 1. Otomatik Test Kapsamı Eksikliği
Birim testleri, entegrasyon testleri veya CI/CD pipeline'ı bulunmuyor. Model mimarisi, veri yükleme ve API endpoint'lerinin otomatik doğrulaması yapılmamaktadır.

## 2. Değerlendirme Verisi Kalitesi
İlk model değerlendirmesi KIDO veri setinde yapılmıştır. Bu veri setinin etiket kalitesi commit'lerden değerlendirilemiyor; etiketlerin kim tarafından ve nasıl üretildiği belgelenmemiştir.

## 3. Pseudo-Etiket Güvenilirliği
~23.000 örnekli highconf manifest, öğretmen model tarafından üretilmiş etiketler içermektedir. Bu etiketler gerçek insan uzman etiketleri değildir. Etiket gürültüsü oranı kesin bilinmemektedir.

## 4. Sınıf Dengesizliği
- Cinsiyet değerlendirmesinde: Female=983, Male=647 (dengesiz)
- Duygu değerlendirmesinde (yeni 4-sınıf): sınıf dağılımı henüz değerlendirme sonuçlarında belgelenmemiş

## 5. Klinisyen Değerlendirmesi Yok
Sistemin klinik değeri, gerçek klinisyenler tarafından değerlendirilmemiştir. Bu, tez için önemli bir sınırlamadır.

## 6. Genelleme Belirsizliği
KIDO veri seti Türk okul çocuklarına aittir. Sistemin farklı kültürel bağlamlarda veya yaş gruplarında ne kadar iyi çalışacağı bilinmemektedir.

## 7. Aktif Geliştirme Durumu
Nisan 2026 sıfırlamasından bu yana `/predict` endpoint'i `503` döndürmektedir. Yeni sistemin ne zaman tamamen devreye gireceği belirsizdir.

---

# Tezde Kullanılabilecek Anlatım

İlk çok modlu sistemin değerlendirilmesinde duygu sınıflandırması görevinde %94.36 doğruluk oranı elde edilmiştir. Bu sonuçlar, çizim tabanlı duygu tespitinin makine öğrenimi yöntemleriyle başarılı bir şekilde gerçekleştirilebileceğine işaret etmektedir. Bununla birlikte, değerlendirmenin sınırlı sayıda epoch ve dondurulmuş BERT ile yapıldığını, klinik doğrulama içermediğini ve yeni 4-sınıflı sistem için henüz kapsamlı değerlendirme tamamlanmadığını belirtmek gereklidir.
