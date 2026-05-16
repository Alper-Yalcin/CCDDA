# Tez Geliştirme Dokümantasyonu — README

Bu klasör, CCDDA projesinin geliştirme sürecini Git commit geçmişi, kaynak kodu ve mevcut dosya yapısından yeniden oluşturan akademik dokümantasyon içermektedir.

---

## Bu Dokümantasyonun Amacı

Tez geliştirme sürecinde her kararın, her denemenin ve her hatanın anlık olarak kayıt altına alınması her zaman mümkün olmaz. Bu dokümantasyon, geliştirme sürecini Git geçmişinden geriye dönük olarak sistematik biçimde yeniden kurarak şu amaçlara hizmet etmektedir:

- Tez yazım sürecine kronolojik geliştirme anlatısı sağlamak
- Teknik kararların ve gerekçelerinin belgelenmesi
- Karşılaşılan problemlerin ve çözüm yaklaşımlarının kayıt altına alınması
- Tezde kullanılabilecek hazır akademik paragraflar sunmak
- Belirsiz veya tahmini bilgileri dürüstçe işaretlemek

---

## Kaynaklar

Bu dokümantasyon aşağıdaki kaynaklardan üretilmiştir:

- Git commit geçmişi (`git log --oneline --reverse`)
- Commit diff'leri (`git show <commit_id>`)
- Mevcut dosya yapısı ve kaynak kodu
- `artifacts/report_run/REPORT.md` (model değerlendirme sonuçları)
- `README.md` (proje kök dizini)
- `api_server.py`, `run_highconf_pipeline.py`, `run_consensus_pipeline.py` içerikleri
- `out/` klasörü çıktı dosyaları

---

## Dosya Listesi

| Dosya | İçerik |
|---|---|
| `00_proje_genel_ozet.md` | Projenin amacı, kullanılan teknolojiler, genel yapı |
| `01_commit_kronolojisi.md` | Tüm commitlerin kronolojik tablosu ve teknik analizi |
| `02_gelistirme_asamalari.md` | Commitler anlamlı geliştirme aşamalarına gruplandı |
| `03_deneyler_ve_denemeler.md` | Alternatif yaklaşımlar ve iptal edilen denemeler |
| `04_karsilasilan_problemler_ve_cozumler.md` | Teknik problemler ve uygulanan çözümler |
| `05_teknik_kararlar.md` | Mimari ve teknoloji seçim kararları |
| `06_sistem_mimarisi_evrimi.md` | Sistemin mimari olarak nasıl değiştiği |
| `07_ozellik_bazli_gelisim.md` | Her özelliğin gelişim süreci |
| `08_hata_duzeltmeleri_ve_refactoring.md` | Bug fix'ler ve kod düzenlemeleri |
| `09_test_dogrulama_ve_sinirlamalar.md` | Test süreci, elde edilen metrikler, sınırlamalar |
| `10_tezde_kullanilabilecek_anlatim.md` | Doğrudan teze aktarılabilecek akademik paragraflar |
| `11_zaman_cizelgesi.md` | Commit tarihlerine dayalı zaman çizelgesi |
| `12_eksik_bilgiler_ve_durust_notlar.md` | Kesin bilinmeyen bilgiler, tahminler, dikkat edilmesi gerekenler |

---

## Tez Yazarken Nasıl Kullanılır

### Geliştirme Metodolojisi İçin
`02_gelistirme_asamalari.md` ve `10_tezde_kullanilabilecek_anlatim.md` — Sistemin nasıl geliştirildiğini anlatmak için.

### Teknik Katkılar İçin
`05_teknik_kararlar.md` ve `06_sistem_mimarisi_evrimi.md` — Mimari kararları ve teknoloji tercihlerini açıklamak için.

### Sonuçlar ve Değerlendirme İçin
`09_test_dogrulama_ve_sinirlamalar.md` — Model performansı ve sınırlamaları için. İçindeki confusion matrix, F1 ve ROC-AUC değerleri belgelenmiştir.

### Dürüstlük ve Şeffaflık İçin
`12_eksik_bilgiler_ve_durust_notlar.md` — Tezde aşırı iddia yapmamak için bu dosyaya mutlaka başvurun.

### Zaman Damgaları İçin
`11_zaman_cizelgesi.md` — "Sistem X tarihi itibarıyla geliştirilmiştir" gibi ifadeler için.

---

## Bilginin Güvenilirlik Düzeyleri

Bu dokümantasyonda üç farklı güvenilirlik düzeyinde bilgi bulunmaktadır:

### Kesin Bilgi (Kanıta Dayalı)
Commit diff'lerinde, kaynak kodunda veya raporlarda açıkça görülen bilgiler. Örnek:
- İlk model F1=0.9435 duygu performansı elde etti
- EfficientNet-B0 ve Türkçe BERT kullanıldı
- `5311334` commit'inde eski AI yığını kaldırıldı

### Tahmini Bilgi (Açıkça İşaretlendi)
"Muhtemelen", "olasılıkla", "commit farkından anlaşıldığı kadarıyla", "tahminen" gibi ifadelerle işaretlenmiş yorumlar. Bunlar makul çıkarımlar olmakla birlikte doğrulanmamıştır.

### Bilinmeyen Bilgi
`12_eksik_bilgiler_ve_durust_notlar.md` dosyasında açıkça listelenen bilgiler. Bunlar tez yazarı tarafından kendi deneyiminden tamamlanmalıdır.

---

## Önemli Uyarı

Bu dokümantasyon **commit geçmişini yorumlayan** bir analizdir. Tez yazarının bizzat deneyimlediği ancak commit'lere yansımayan süreçler (danışman görüşmeleri, el yazısı notlar, yerel denemeler, klinisyen geri bildirimleri vb.) bu dosyalarda yer almamaktadır.

Tez yazarı, bu dokümantasyonu başlangıç noktası olarak kullanmalı; kendi bilgi ve deneyimiyle zenginleştirmeli ve belirsiz noktaları netleştirmelidir.

---

*Bu dokümantasyon, Claude Code tarafından Git commit geçmişi analizi yoluyla oluşturulmuştur (Mayıs 2026).*
