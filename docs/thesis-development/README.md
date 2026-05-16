# Tez Geliştirme Dokümantasyonu — README

Bu klasör, CCDDA projesinin geliştirme sürecini Git commit geçmişi, kaynak kodu, metrik dosyaları ve pipeline çıktılarından yeniden oluşturan akademik dokümantasyon içermektedir.

---

## Bu Dokümantasyonun Amacı

Bu dokümantasyon, geliştirme sürecini commit geçmişi ve repository içindeki somut kanıtlardan sistematik biçimde yeniden kurarak şu amaçlara hizmet etmektedir:

- Tez yazım sürecine kronolojik geliştirme anlatısı sağlamak
- Teknik kararların kanıt kaynaklarıyla belgelenmesi
- Elde edilen performans metriklerinin ve karşılaştırmaların kayıt altına alınması
- Tezde kullanılabilecek akademik paragraflar sunmak
- Kanıt bulunmayan kararlar için bunu açıkça belirtmek

---

## Kaynaklar

Bu dokümantasyon aşağıdaki kaynaklardan üretilmiştir:

- Git commit geçmişi ve diff'leri
- `artifacts/report_run/REPORT.md` (ilk multimodal model metrikleri)
- `artifacts/v1_backend/eval/metrics.json` (4-sınıf test sonuçları, 1.257 örnek)
- `artifacts/v1_backend/train/train.log` (epoch bazlı training/validation logları)
- `artifacts/v1_backend/eval/confusion_matrix.csv` (4-sınıf confusion matrix)
- `artifacts/v1_backend/eval/calibration.json` (ECE ve güven analizi)
- `artifacts/v1_backend/eval/high_confidence_errors.csv` (yüksek güvenilirlikli hatalar)
- `out/highconf_pipeline/summary_results.csv` (0.75 ve 0.85 eşik karşılaştırması)
- `out/consensus_pipeline/summary_results.csv` (consensus pipeline sonuçları)
- `out/highconf_pipeline/teacher_labels_report.json` (öğretmen model istatistikleri)
- `out/phenotype_images/multitask_run_alpha025/test_results.json` (multitask sonuçları)
- `api_server.py`, `run_highconf_pipeline.py`, `run_consensus_pipeline.py` kaynak kodları

---

## Dosya Listesi

| Dosya | İçerik |
|---|---|
| `00_proje_genel_ozet.md` | Projenin amacı, kullanılan teknolojiler, genel yapı |
| `01_commit_kronolojisi.md` | Tüm commitlerin kronolojik tablosu ve diff analizleri |
| `02_gelistirme_asamalari.md` | Commitler anlamlı geliştirme aşamalarına gruplandı |
| `03_deneyler_ve_denemeler.md` | Deneylerin kanıta dayalı karşılaştırmaları ve sonuçları |
| `04_karsilasilan_problemler_ve_cozumler.md` | Teknik problemler ve ölçülen çözüm etkileri |
| `05_teknik_kararlar.md` | Mimari ve teknoloji seçim kararları |
| `06_sistem_mimarisi_evrimi.md` | Sistemin mimari olarak nasıl değiştiği |
| `07_ozellik_bazli_gelisim.md` | Her özelliğin gelişim süreci |
| `08_hata_duzeltmeleri_ve_refactoring.md` | Bug fix'ler ve kod düzenlemeleri |
| `09_test_dogrulama_ve_sinirlamalar.md` | Tüm modellerin test metrikleri, confusion matrix, kalibrasyon |
| `10_tezde_kullanilabilecek_anlatim.md` | Doğrudan teze aktarılabilecek akademik paragraflar (kanıta dayalı) |
| `11_zaman_cizelgesi.md` | Commit tarihlerine dayalı zaman çizelgesi |
| `12_eksik_bilgiler_ve_durust_notlar.md` | Kanıt bulunmayan kararlar ve tez yazarının eklemesi gereken bilgiler |
| `13_tam_dokumantasyon_birlestirme.md` | Tüm dosyaların tek belgede birleşimi |

---

## Tez Yazarken Nasıl Kullanılır

### Geliştirme Metodolojisi İçin
`02_gelistirme_asamalari.md` ve `10_tezde_kullanilabilecek_anlatim.md`

### Teknik Katkılar İçin
`05_teknik_kararlar.md` ve `06_sistem_mimarisi_evrimi.md`

### Sonuçlar ve Değerlendirme İçin
`09_test_dogrulama_ve_sinirlamalar.md` — 7 farklı model/pipeline'ın karşılaştırmalı sonuçları mevcuttur.

### Kanıt Bulunmayan Kararlar İçin
`12_eksik_bilgiler_ve_durust_notlar.md` — Hangi kararların teknik gerekçesinin belgelenmediğini listeler.

### Zaman Damgaları İçin
`11_zaman_cizelgesi.md`

---

## Bilginin Güvenilirlik Düzeyleri

### Kanıta Dayalı Bilgi
Repository içindeki dosyalardan (metrik JSON'ları, training logları, confusion matrix CSV'leri, pipeline raporları, commit diff'leri) doğrudan alınan bilgiler. Kaynak dosya her zaman belirtilmiştir.

### Kanıt Bulunmayan Bilgi
"Repository içinde bu kararın teknik gerekçesini doğrulayan metrik veya log bulunamadı." ifadesiyle açıkça işaretlenmiştir. Bu belgede spekülatif ifade ("muhtemelen", "olabilir", "tahminen") kullanılmamıştır.

---

## Önemli Not

Bu dokümantasyon yalnızca repository içindeki somut kanıtları yansıtmaktadır. Commit geçmişine yansımayan kararlar (danışman görüşmeleri, yerel denemeler, klinik geri bildirimler) bu dosyalarda yer almamaktadır. Bu tür bilgilerin tez yazarı tarafından eklenmesi gerekmektedir.

---

*Bu dokümantasyon, forensic repository analizi yoluyla oluşturulmuştur (Mayıs 2026).*
