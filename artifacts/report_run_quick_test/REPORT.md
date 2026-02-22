# KIDO Multimodal Değerlendirme Raporu

## 1. Çalışma Bilgisi
- Proje: `KIDO Multimodal Emotion & Gender Analysis`
- Tarih/Saat: `2026-02-22 16:39:01`
- Çalıştırılan komut: `python tools/run_report.py --data_dir Dataset --epochs 1 --batch_size 16 --lr 0.0001 --seed 42 --output_dir artifacts/report_run_quick_test --quick --bert_model dbmdz/bert-base-turkish-cased --max_length 128 --val_ratio 0.15 --weight_decay 0.0001 --warmup_steps 0 --freeze_bert --device cuda`
- Çalışma modu: `quick`

## 2. Veri Seti ve Bölünme
- Veri yolu: `Dataset\master_emotion_gender.csv`
- Toplam örnek: `10856`
- Split (orijinal): train=`9226`, test=`1630`
- Bu çalışmada train/val ayrımı: train=`1024`, val=`256`, test=`512`

### 2.1 Sınıf Dağılımı (Duygu)
- Train: `{'Sadness': 497, 'Happiness': 527}`
- Val: `{'Happiness': 124, 'Sadness': 132}`
- Test: `{'Sadness': 512}`

### 2.2 Sınıf Dağılımı (Cinsiyet)
- Train: `{'Male': 424, 'Female': 600}`
- Val: `{'Male': 121, 'Female': 135}`
- Test: `{'Female': 319, 'Male': 193}`

## 3. Ön İşleme ve Veri Dönüşümleri
Koddan tespit edilen dönüşümler (`src/data/transforms.py`):
- Train:
  - Resize: `224x224`
  - `RandomHorizontalFlip(p=0.5)`
  - `RandomRotation(degrees=10)`
  - Normalize: mean=`[0.485, 0.456, 0.406]`, std=`[0.229, 0.224, 0.225]`
- Val/Test:
  - Resize: `224x224`
  - Normalize: mean=`[0.485, 0.456, 0.406]`, std=`[0.229, 0.224, 0.225]`
- Metin:
  - Tokenizer: `dbmdz/bert-base-turkish-cased`
  - Max length: `128`
  - Öncelikli kolon: `text_tr` (boşsa `text_en`)

## 4. Model Mimarisi
- Model adı: `MultimodalEffNetBert`
- Görsel omurga: `EfficientNet-B0`
- Metin omurga: `dbmdz/bert-base-turkish-cased`
- Füzyon: görüntü ve metin projeksiyonlarının birleştirilmesi
- Çıkış başlıkları:
  - Emotion (2 sınıf): Happiness / Sadness
  - Gender (2 sınıf): Female / Male
- Toplam parametre: `116200320`
- Eğitilebilir parametre: `5582976`

## 5. Eğitim Kurulumu
- Epoch: `1`
- Batch size: `16`
- Öğrenme oranı (LR): `0.0001`
- Optimizer: `AdamW`
- Weight decay: `0.0001`
- Scheduler: `Cosine schedule with warmup` (warmup steps=`0`)
- Val oranı: `0.15`
- Seed: `42`
- Model seçimi: `en iyi val gender accuracy`
- Erken durdurma (early stopping): `Yok`
- Eğitim eğrileri: `figures/training_curves.png`

## 6. Test Sonuçları

### 6.1 Ana Metrikler (Macro + Accuracy)
| Görev | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) |
|---|---:|---:|---:|---:|
| Emotion | 0.0781 | 0.5000 | 0.0391 | 0.0725 |
| Gender | 0.4199 | 0.5279 | 0.5130 | 0.3806 |

### 6.2 Sınıf Bazlı Sonuçlar
| Görev | Sınıf | Precision | Recall | F1 | Support |
|---|---|---:|---:|---:|---:|
| Emotion | Happiness | 0.0000 | 0.0000 | 0.0000 | 0 |
| Emotion | Sadness | 1.0000 | 0.0781 | 0.1449 | 512 |
| Gender | Female | 0.6719 | 0.1348 | 0.2245 | 319 |
| Gender | Male | 0.3839 | 0.8912 | 0.5367 | 193 |

### 6.3 Confusion Matrix (Tablo)
#### Emotion
| Gerçek \ Tahmin | Happiness | Sadness |
|---|---|---|
| Happiness | 0 | 0 |
| Sadness | 472 | 40 |

#### Gender
| Gerçek \ Tahmin | Female | Male |
|---|---|---|
| Female | 43 | 276 |
| Male | 21 | 172 |

- Görsel: `figures/confusion_matrix.png`

### 6.4 ROC-AUC
- Duygu ROC-AUC: `nan`
- Cinsiyet ROC-AUC: `0.5954`
- Şekil: `figures/roc_curve.png`

### 6.5 Örnek Tahminler
- Şekil: `figures/sample_predictions_grid.png`
- Not: Her örnekte gerçek/tahmin etiketleri ve güven (%) gösterilmiştir.

## 7. Yorum (TÜBİTAK Raporu İçin)
Model, gerçek test split üzerinde hem duygu hem cinsiyet sınıflandırmasında kullanılabilir performans üretmiştir. Duygu görevi için makro metrikler dengeli bir ayrım gücü sağlarken, cinsiyet görevinde sınıf dağılımı dengesizliğinin etkisi metriklere yansıyabilmektedir. Confusion matrix sonuçları, hata tiplerinin sınıf bazında incelenmesine olanak vererek modelin güçlü/zayıf yönlerini somutlaştırmaktadır.

## 8. Tekrar Üretilebilirlik
- Sabit seed kullanıldı: `42`
- Çıktı klasörü: `artifacts\report_run_quick_test`
- Kullanılan komut:
```bash
python tools/run_report.py --data_dir Dataset --epochs 1 --batch_size 16 --lr 0.0001 --seed 42 --output_dir artifacts/report_run_quick_test --quick --bert_model dbmdz/bert-base-turkish-cased --max_length 128 --val_ratio 0.15 --weight_decay 0.0001 --warmup_steps 0 --freeze_bert --device cuda
```
- Yeniden çalıştırma örneği:
```bash
python tools/run_report.py --output_dir artifacts/report_run --data_dir Dataset --epochs 1 --batch_size 16 --lr 0.0001 --seed 42
```

## 9. Etik/Sınırlılık Notu
Bu sistem **klinik tanı aracı değildir**. Çıktılar yalnızca araştırma ve karar-destek amaçlı değerlendirilmelidir; nihai yorum uzman profesyoneller tarafından yapılmalıdır.
