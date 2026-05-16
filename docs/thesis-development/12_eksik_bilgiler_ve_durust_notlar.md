# 12 — Eksik Bilgiler ve Dürüst Notlar (Güncellenmiş)

Bu dosya, forensic repository analizi sonrasında hâlâ kanıtlanamayan bilgileri ve tez yazarına yönelik dürüst uyarıları içermektedir. Repository içindeki metrik dosyaları, training logları ve pipeline raporları incelendikten sonra güncellenmiştir.

---

# Forensic Analizden Sonra Netleşen Bilgiler

Aşağıdaki bilgiler önceki versiyonda belirsizdi; şimdi somut kanıt mevcuttur:

| Konu | Önceki Durum | Şimdiki Kanıt | Kaynak |
|---|---|---|---|
| 0.75 vs 0.85 threshold karşılaştırması | Bilinmiyor | 0.75: F1=0.6694 (daha iyi); 0.85: F1=0.6495 | `out/highconf_pipeline/summary_results.csv` |
| Consensus pipeline performansı | Bilinmiyor | Accuracy=57.49%, F1=0.5721 (highconf'tan düşük) | `out/consensus_pipeline/summary_results.csv` |
| Multitask öğrenme sonucu | Bilinmiyor | Accuracy=72.73%, F1=0.7272 (en iyi 4-sınıf sonuç) | `out/phenotype_images/multitask_run_alpha025/test_results.json` |
| 4-sınıf temel model performansı | Bilinmiyor | Accuracy=67.06%, F1=0.5775 | `artifacts/v1_backend/eval/metrics.json` |
| Overfitting kanıtı | Tahmindi | Train F1=0.9039 vs Val F1=0.6135 (0.29 fark) | `artifacts/v1_backend/train/train.log` |
| Kalibrasyon kalitesi | Bilinmiyor | ECE=0.1698 (overconfident) | `artifacts/v1_backend/eval/calibration.json` |
| Öğretmen model etiket dağılımı | Bilinmiyor | Angry=19.211 (en çok), Fear=10.388 (en az) | `out/highconf_pipeline/teacher_labels_report.json` |
| Toplam pseudo-etiketleme kapsamı | Bilinmiyor | 55.660 görüntü etiketlendi | `out/highconf_pipeline/teacher_labels_report.json` |

---

# Hâlâ Kanıtlanamayan Bilgiler

## 1. Multimodal Mimariden Vazgeçilmesinin Teknik Nedeni

**Durum:** Repository içinde bu kararın teknik nedenini doğrulayan log veya metrik bulunamadı.

**Mevcut kanıt:** Commit `5311334` mesajı yalnızca "chore: remove legacy dataset and reset old AI stack" demektedir; performans karşılaştırması, ablation study veya başarısızlık logu içermemektedir.

**Tez yazarı eklemelidir:** Bu kararın gerçek nedeni (danışman önerisi mi? Performans sorunu mu? Kapsam değişikliği mi?).

## 2. KIDO Veri Setinin Kaynağı ve Etiketleme Süreci

**Durum:** Repository içinde etiketleme protokolü, etiketleyen kişi/kurum ve güvenilirlik analizi bulunamadı.

**Mevcut kanıt:** Yalnızca dosya adı şeması (`[okul_id]-[sınıf]-[öğrenci_id]-[cinsiyet]-[duygu].jpg`).

**Tez için kritik:** Etiketlerin kaynağı ve güvenilirliği tezde mutlaka belgelenmelidir.

## 3. Sessiz Dönemlerdeki Çalışmalar

Tespit edilen üç sessiz dönem:
- Aralık 2025 – Şubat 2026 (~3 ay)
- Mart–Nisan 2026 (~5 hafta)
- Nisan–Mayıs 2026 (~2.5 hafta)

Bu dönemlerde neler yapıldığı commit geçmişinde görünmemektedir.

## 4. Çok Modlu Modelde Metin Verisinin İçeriği

`dbmdz/bert-base-turkish-cased` modeli kullanılmış; ancak BERT'e verilen metin verisinin tam olarak ne olduğu (öğretmen açıklamaları? meta veriler? başka bir kaynak?) commit geçmişinden belirlenemiyor.

## 5. Klinik Geçerlilik

Repository içinde bir klinisyen veya psikoloji uzmanının sistemi değerlendirdiğine dair belge bulunmamaktadır.

## 6. Consensus Pipeline Sad F1=0.30'un Nedeni

Consensus pipeline neden Sad sınıfında F1=0.30 elde ettiği, bunu açıklayan analiz logu bulunamadı. Mevcut kanıt yalnızca sonucu göstermektedir.
Kaynak: `out/consensus_pipeline/summary_results.csv`

## 7. Etik Kurul Onayı

Çocuklara ait veri toplandığı için etik kurul onay bilgisi tez için kritiktir. Repository içinde bu belge bulunmamaktadır.

## 8. HuggingFace ve Roboflow Veri Setlerinin Lisans Durumu

Harici veri setlerinin lisansları tez yazarı tarafından doğrulanmalıdır.

---

# Tez Yazarken Dikkat Edilmesi Gerekenler (Kanıta Dayalı)

### 1. %94 ile %67 doğruluk karşılaştırılmamalı
- %94.36: 2-sınıflı, dengeli test seti (Happy=815, Sad=815), 5 epoch eğitim
- %67.06: 4-sınıflı, dengesiz test seti (Happy=626, Angry=67), farklı model
Bu iki rakam farklı görevler için olup doğrudan karşılaştırma yanıltıcıdır.
Kaynak: `artifacts/report_run/REPORT.md`, `artifacts/v1_backend/eval/metrics.json`

### 2. "Consensus pipeline daha güvenilir" yazılmamalı
Kanıt: Consensus pipeline Macro F1=0.5721 iken Highconf 0.75 pipeline Macro F1=0.6694. Consensus pipeline her metrikte highconf pipeline'ının altında kalmıştır.
Kaynak: `out/consensus_pipeline/summary_results.csv`, `out/highconf_pipeline/summary_results.csv`

### 3. Pseudo-etiket sayısı gerçek etiket olarak sunulmamalı
23.063 "pseudo-etiketli örnek" uzman etiketli değildir. ECE=0.1698 göz önünde bulundurulduğunda, yüksek güven skoru bile doğruluğu garanti etmemektedir.
Kaynak: `artifacts/v1_backend/eval/calibration.json`

### 4. Klinik doğrulama olmadığını belirtmek şart
Sistem klinisyen tarafından doğrulanmamıştır. "Araştırma prototipi" olarak tanımlanmalıdır.

### 5. Öğretmen model Angry sınıfına bias'lıdır
Öğretmen model 19.211 Angry etiketi üretmiş, ancak aynı modelin Angry F1=0.370. Bu bias pseudo-etiket kalitesini etkilemiştir.
Kaynak: `out/highconf_pipeline/teacher_labels_report.json`, `artifacts/v1_backend/eval/metrics.json`

---

# Tez Yazarının Eklemesi Gereken Bilgiler

- [ ] Multimodal mimariden vazgeçilmesinin gerçek nedeni
- [ ] KIDO veri setinin kaynağı ve etiketleme protokolü
- [ ] Tez danışmanının yönlendirmeleri
- [ ] Sessiz dönemlerde yapılan çalışmalar
- [ ] Klinik değerlendirme sonuçları (varsa)
- [ ] Etik kurul onay durumu
- [ ] Harici veri setlerinin lisans bilgileri
- [ ] Projenin tam tez başlığı ve araştırma sorusu

---

# Forensic Analiz Kaynak Referansları

| Dosya | İçerik |
|---|---|
| `artifacts/report_run/REPORT.md` | İlk multimodal model metrikleri |
| `artifacts/v1_backend/eval/metrics.json` | 4-sınıf temel model, 1257 test örneği |
| `artifacts/v1_backend/eval/confusion_matrix.csv` | 4-sınıf confusion matrix |
| `artifacts/v1_backend/train/train.log` | Epoch bazlı training/validation metrikleri |
| `artifacts/v1_backend/eval/calibration.json` | ECE ve güven analizi |
| `artifacts/v1_backend/eval/high_confidence_errors.csv` | Yüksek güvenle yanlış tahminler |
| `out/highconf_pipeline/summary_results.csv` | Pipeline karşılaştırma sonuçları |
| `out/consensus_pipeline/summary_results.csv` | Consensus pipeline sonuçları |
| `out/highconf_pipeline/teacher_labels_report.json` | Öğretmen model istatistikleri |
| `out/phenotype_images/multitask_run_alpha025/test_results.json` | Multitask model sonuçları |
