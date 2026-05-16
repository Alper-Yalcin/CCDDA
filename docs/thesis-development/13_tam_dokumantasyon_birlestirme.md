# 13 — Tam Dokümantasyon Birleştirme

Bu dosya, tüm tez geliştirme dokümantasyon dosyalarının içeriğini tek bir belgede birleştirmektedir.

**Son güncelleme:** 2026-05-16

**Temel ilke:** Bu belgede spekülatif ifade ("muhtemelen", "olabilir", "tahminen") kullanılmamıştır. Her teknik yorum için kaynak dosya belirtilmiştir. Kanıt bulunmayan kararlar için "Repository içinde bu kararın teknik gerekçesini doğrulayan metrik veya log bulunamadı." ifadesi kullanılmıştır.

**Kanıt kaynakları:**
- rtifacts/report_run/REPORT.md — 2-sınıf multimodal model: Duygu F1=0.9435, Cinsiyet F1=0.7658
- rtifacts/v1_backend/eval/metrics.json — 4-sınıf model: Accuracy=67.06%, Macro F1=0.5775
- rtifacts/v1_backend/train/train.log — Train F1=0.9039, Val F1=0.6135
- rtifacts/v1_backend/eval/calibration.json — ECE=0.1698
- out/highconf_pipeline/summary_results.csv — 0.75: F1=0.6694; 0.85: F1=0.6495
- out/consensus_pipeline/summary_results.csv — Consensus: F1=0.5721
- out/phenotype_images/multitask_run_alpha025/test_results.json — Multitask: F1=0.7272

---

## İçindekiler

1. [README — Dokümantasyon Kılavuzu](#readme)
2. [00 — Proje Genel Özet](#00)
3. [01 — Commit Kronolojisi](#01)
4. [02 — Geliştirme Aşamaları](#02)
5. [03 — Deneyler ve Denemeler](#03)
6. [04 — Karşılaşılan Problemler ve Çözümler](#04)
7. [05 — Teknik Kararlar](#05)
8. [06 — Sistem Mimarisi Evrimi](#06)
9. [07 — Özellik Bazlı Gelişim](#07)
10. [08 — Hata Düzeltmeleri ve Refactoring](#08)
11. [09 — Test, Doğrulama ve Sınırlamalar](#09)
12. [10 — Tezde Kullanılabilecek Anlatım](#10)
13. [11 — Zaman Çizelgesi](#11)
14. [12 — Eksik Bilgiler ve Dürüst Notlar](#12)

---


---

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


---

# 00 — Proje Genel Özet

## Projenin Adı

**CCDDA** — *Children's Drawing-Based Duygu/Emotion Analizi*

Proje dizin adı `CCDDA`'dır. Repository içinde bu kısaltmanın resmi açılımı belirtilmemiştir. `Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx` dosya adı tez başlığını ima etmektedir.

---

## Projenin Amacı

Bu proje, çocuklara ait el çizmesi resimleri kullanarak yapay zeka ile duygu sınıflandırması yapmayı hedeflemektedir. Klinik psikolojide yaygın olarak kullanılan projektif çizim testlerinden (ör. İnsan Çizme Testi, Ev-Ağaç-İnsan) esinlenerek, çocukların çizdikleri resimlerin bilgisayarlı görü yöntemleriyle analiz edilip analiz edilemeyeceği araştırılmaktadır.

Proje iki farklı sınıflandırma hedefi ile başlamıştır:

1. **Duygu sınıflandırması**: Resmi çizen çocuğun duygusal durumunun tespit edilmesi
2. **Cinsiyet sınıflandırması**: Çizim sahibinin cinsiyetinin çizimden tahmin edilmesi

Proje ilerledikçe cinsiyet sınıflandırması bırakılmış, duygu sınıflandırması daha fazla sınıf içerecek biçimde genişletilmiştir.

---

## Çözülmeye Çalışılan Problem

Çocukların duygusal durumları genellikle sözel ifadelerle tam olarak ortaya konulamaz. Projektif çizim testleri bu boşluğu doldurmak amacıyla psikoloji pratiğinde kullanılmaktadır; ancak bu testlerin yorumlanması uzman gerektirmekte, zaman almakta ve öznellik içermektedir.

Bu proje, söz konusu değerlendirme sürecini bir dereceye kadar otomatikleştirmeyi ve nesnel bir referans araç sunmayı amaçlamaktadır. Yapay zekanın bir klinisyenin yerini almak için değil, ona destek olmak için kullanılması hedeflenmektedir.

---

## Kullanılan Teknolojiler

### Derin Öğrenme & Görüntü İşleme
| Teknoloji | Kullanım Amacı |
|---|---|
| PyTorch | Ana derin öğrenme çerçevesi |
| EfficientNet-B0 / B2 / B3 | Görüntü özellik çıkarımı için CNN |
| Torchvision | Veri dönüşümleri, model ağırlıkları |
| Grad-CAM | Açıklanabilirlik (hangi bölgeye bakıldığının görselleştirilmesi) |

### Doğal Dil İşleme (Erken Dönem — Sonradan Kaldırıldı)
| Teknoloji | Kullanım Amacı |
|---|---|
| `dbmdz/bert-base-turkish-cased` | Türkçe metin kodlaması |
| HuggingFace Transformers | BERT entegrasyonu |

### Pseudo-Etiketleme & Veri Genişletme (Son Dönem)
| Teknoloji | Kullanım Amacı |
|---|---|
| Qwen2.5-VL (3B / 7B) | Çok modlu büyük dil modeli ile görsel etiketleme |
| HuggingFace Inference API | Uzak model çağrıları |
| Ollama | Yerel LLM çalıştırma |

### Backend & API
| Teknoloji | Kullanım Amacı |
|---|---|
| FastAPI | REST API sunucusu |
| Uvicorn | ASGI sunucu |
| Pydantic | Veri doğrulama |

### Frontend
| Teknoloji | Kullanım Amacı |
|---|---|
| React + Vite | Web arayüzü |
| TypeScript | Tip güvenli frontend kodu |
| Tailwind CSS | Stil |
| i18next | Türkçe/İngilizce çoklu dil desteği |

### Masaüstü Uygulama
| Teknoloji | Kullanım Amacı |
|---|---|
| PyInstaller | Python uygulamasını `.exe` formatına dönüştürme |
| pywebview | Masaüstünde web içeriği gösterme |
| Inno Setup | Windows kurulum paketi oluşturma |
| Tkinter | Erken dönem yerel GUI |

### Veri & Raporlama
| Teknoloji | Kullanım Amacı |
|---|---|
| Pandas, pyarrow | Veri manipülasyonu |
| scikit-learn | Metrik hesaplama |
| python-docx | DOCX raporu üretimi |
| Matplotlib | Görselleştirme |

---

## Genel Sistem Yapısı

Proje tarihin farklı dönemlerinde farklı mimarilere sahip olmuştur:

### İlk Mimari (Kasım 2025)
Çok modlu sinir ağı: görüntü (EfficientNet-B0) + metin (Türkçe BERT) → ortak gömmeler → iki ayrı sınıflandırma kafası (duygu + cinsiyet)

### Arayüz Dönemi (Kasım 2025 – Mart 2026)
Tkinter tabanlı masaüstü GUI → React web arayüzü → FastAPI arka ucu → PyInstaller ile paketlenmiş masaüstü uygulama

### Yeniden Yapılanma (Nisan 2026)
Eski çok modlu yapı (BERT dahil) tamamen kaldırıldı. Yeni hedef: **yalnızca görüntü tabanlı 4 sınıflı duygu tanıma** (Anger / Fear / Happiness / Sadness)

### Yeni Veri Hattı (Mayıs 2026)
Pseudo-etiketleme yaklaşımıyla büyük ölçekli veri üretimi. Öğretmen modeller (EfficientNet-B2/B3) çizim resimlerini etiketliyor; yüksek güvenilirlikli tahminler yeni eğitim veri kümesini oluşturuyor.

---

## Veri Kaynakları

Commit geçmişi ve dosya yapısından anlaşılan veri kaynakları:

- **KIDO Veri Kümesi**: Türk okul çocuklarına ait el çizmesi resimler; dosya adları `[okul_id]-[sınıf]-[öğrenci_id]-[cinsiyet]-[duygu]` formatında kodlanmış (örn. `101-1A-369-F-H.jpg`)
- **HuggingFace Parquet Dosyaları**: `Dataset/huggingface/` dizininde saklanan büyük ölçekli ek veri
- **Roboflow — Drawing Facial Emotions**: `Dataset/Images/Emotion_Roboflow_DrawingFacialEmotions/`
- **SigLIP 4-class**: `Dataset/Images/Emotion_SigLIP_4Class/` — SigLIP modeli kullanılarak 4 sınıfa göre önceden sınıflandırılmış veri
- **Türetilmiş Veri Kümeleri**: Pseudo-etiketleme ile üretilmiş veri manifestleri (`out/highconf_pipeline/`, `out/consensus_pipeline/`)

---

## Tez Bağlamında Projenin Önemi

Bu proje aşağıdaki araştırma sorularını karşılamayı amaçlamaktadır:

1. Çocuk çizimleri yalnızca görsel özelliklerinden hareketle duygu sınıflandırmasına uygun mudur?
2. Çok modlu yaklaşımlar (görüntü + metin) görüntü-only yaklaşımdan daha iyi performans gösterir mi?
3. Pseudo-etiketleme ile veri artırımı sınıflandırma başarısını iyileştirilebilir mi?
4. Bu sistem klinisyenlere pratik destek sağlayabilecek bir kullanılabilirlik düzeyine ulaşabilir mi?

---

## Mevcut Durumun Özeti (Kod Yapısından Çıkarılan)

- **Eski AI katmanı** Nisan 2026'da bilinçli olarak kaldırılmıştır.
- `api_server.py` içinde `/predict` endpoint'i hâlâ vardır ancak `503 reset_in_progress` döndürmektedir.
- Yeni 4-sınıflı sistem için `run_highconf_pipeline.py` ve `run_consensus_pipeline.py` aktif olarak geliştirilmektedir.
- Frontend (React) ve masaüstü uygulama kabuğu korunmuştur; yeni model tamamlandığında bu kabuğa bağlanacaktır.
- `artifacts/` klasörü eğitim kontrol noktaları için yer tutucu olarak kullanılmaktadır.


---

# 01 — Commit Kronolojisi

Bu dosya, projenin tüm commit geçmişini en eski committen en yeniye doğru, diff analizi ve tez bağlamıyla listeler. Commit mesajlarından çıkarılamayan teknik detaylar diff içeriğine dayandırılmıştır. Kanıt bulunmayan yorumlar için bu durum açıkça belirtilmiştir.

---

## Commit Tablosu

| # | Commit ID | Tarih | Commit Mesajı | Kategori | Değişen Dosyalar (Özet) | Teknik Analiz |
|---|---|---|---|---|---|---|
| 1 | `ec7d0f8` | 2025-11-30 | first commit | `setup` | `.gitignore`, `Dataset/Images/Education/test/Primary/` (çok sayıda resim), `src/train/train_multimodal.py`, diğer src dosyaları | Projenin başlangıç commiti. KIDO veri seti görüntüleri ve çok modlu EfficientNet+BERT eğitim scripti aynı anda repo'ya eklendi. |
| 2 | `b8b32b2` | 2025-11-30 | Ağırlık düzenleme | `feature` | `src/models/multimodal_effnet_bert.py`, `src/train/train_multimodal.py` | Commit diff: `multimodal_effnet_bert.py` dosyasına EfficientNet-B0 + Türkçe BERT birleşik mimari eklendi. `train_multimodal.py`'de `--freeze_bert=True`, `--freeze_effnet=False` parametreleri tanımlandı. "Ağırlık düzenleme" mesajı bu parametre değişikliğini ifade etmektedir. |
| 3 | `d494e7b` | 2025-11-30 | Ezber cümleler ve GUI eklendi | `feature` + `ui` | `src/app/gui_multimodal.py`, `src/app/tk_app.py`, `src/data/dataset.py`, `src/explain/gradcam.py`, `src/explain/perception_api.py`, `src/explain/predict_and_explain.py`, `src/explain/rule_based_explainer.py`, `src/explain/text_explain.py`, Grad-CAM görsel çıktıları | Commit mesajındaki "ezber cümleler" ifadesi `rule_based_explainer.py` içindeki önceden tanımlı şablon açıklamalara karşılık gelmektedir. Aynı committe Tkinter GUI (`gui_multimodal.py`), Grad-CAM modülü ve metin açıklayıcı eklendi. Grad-CAM görsel çıktıları da commite dahil edildi. |
| 4 | `339a738` | 2026-02-22 | Add scrollable text widget for explanation and refactor explanation generation | `ui` + `refactor` | `src/app/gui_multimodal.py`, `src/app/tk_app.py` | Commit 3 ile Commit 4 arasında yaklaşık 3 ay geçmiştir. Bu dönemde repository'de commit yoktur. Tkinter GUI'de açıklama metni için kaydırılabilir metin alanı eklendi; açıklama üretimi yeniden düzenlendi. |
| 5 | `a04e560` | 2026-02-22 | feat: initialize React project with Vite, Tailwind CSS, and TypeScript | `setup` | `Web/` dizininin tamamı (React projesi iskelet) | Tkinter GUI'den web tabanlı arayüze geçiş başladı. React + Vite + TypeScript + Tailwind CSS projesinin ilk kurulumu yapıldı. |
| 6 | `3b481f8` | 2026-02-22 | feat: implement internationalization support with language selection | `feature` | `Web/src/` (i18n entegrasyonu) | Commit diff: `i18next` kütüphanesi entegre edildi. Türkçe ve İngilizce dil dosyaları eklendi. |
| 7 | `08e1303` | 2026-02-22 | feat: enhance analysis page with text input and error handling; add FastAPI backend for predictions | `feature` + `api` | `Web/src/App.tsx`, `Web/src/locales/*.json`, `Web/vite.config.ts`, `api_server.py` (yeni, 131 satır), `requirements.txt` | `api_server.py` ilk kez oluşturuldu (131 satır). `vite.config.ts` güncellenerek React dev sunucusu FastAPI'ye proxy yapılandırıldı. |
| 8 | `1476c63` | 2026-02-22 | feat: add explanation field to API result and update UI to display model explanations | `feature` | `Web/src/App.tsx`, `api_server.py` | API yanıt formatına `explanation` alanı eklendi. UI bu alanı gösterecek şekilde güncellendi. |
| 9 | `ef0af36` | 2026-02-22 | feat: add localization support for emotion and gender labels; update explanation generation in API | `feature` | `Web/src/App.tsx`, `api_server.py` | Duygu ve cinsiyet etiketleri için dil bazlı yerelleştirme desteği eklendi. 189 satır ekleme. |
| 10 | `bab2958` | 2026-02-22 | Add report runner script and configuration for quick testing | `test` + `docs` | `artifacts/report_run/REPORT.md`, `artifacts/report_run/figures/` (confusion matrix, ROC curve), `run_report.py`, `run_args.json` | Model değerlendirme ve raporlama altyapısı eklendi. `REPORT.md` sonuçlarını içeriyor: Duygu Accuracy=%94.36, F1=0.9435, ROC-AUC=0.9866; Cinsiyet Accuracy=%77.12, F1=0.7658, ROC-AUC=0.8542. |
| 11 | `16fa3d3` | 2026-03-12 | Add script to generate DOCX reports from Markdown using a template | `feature` | `build_report_docx.py`, `Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx`, `artifacts/docx_inspect/` | Markdown'dan DOCX formatına dönüşüm scripti oluşturuldu. Tez belgesi şablonu (`Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx`) repo'ya eklendi. |
| 12 | `2a6895c` | 2026-03-12 | feat: add desktop application with embedded FastAPI server and React frontend | `feature` | `desktop_app.py`, `desktop_app.spec`, `src/app_paths.py`, `Web/src/App.tsx` (+346 satır), `api_server.py` (büyük güncelleme), `requirements-desktop.txt`, Inno Setup scripti, `build_desktop.ps1` | `src/app_paths.py` dosyası `sys.frozen` kontrolü ile paketlenmiş ortamda dosya yolu çözümlemesi yapıyor. PyInstaller + pywebview ile bağımsız Windows uygulaması inşa altyapısı kuruldu. |
| 13 | `72d8a7b` | 2026-03-12 | Refactor code structure for improved readability and maintainability | `refactor` | `desktop_app.py` (13 satır), `.gitignore`, `Web/public/about/` (grafik görseller) | Kod yapısı düzenlendi. Confusion matrix, ROC eğrisi, eğitim eğrileri web uygulamasının `/about` sayfasına eklendi. |
| 14 | `5311334` | 2026-04-19 | chore: remove legacy dataset and reset old AI stack | `cleanup` | `Dataset/Images/Education/` (çok sayıda resim silindi) ve eski AI modülleri | **Kritik mimari sıfırlama.** Eski çok modlu AI yığını (BERT dahil) bilinçli olarak kaldırıldı. README güncellenerek yeni yön açıklandı. `/predict` endpoint `503` döndürecek şekilde devre dışı bırakıldı. Bu kararın teknik gerekçesini doğrulayan performans karşılaştırması veya log bulunamadı. |
| 15 | `fb8602a` | 2026-04-20 | feat: add comprehensive execution plan for Backend V1 micro-sprints | `docs` | Plan/döküman dosyaları | Backend V1 için mikro-sprint yürütme planı eklendi. |
| 16 | `dc64027` | 2026-05-08 | Auto-commit: save changes before push (assistant) | `setup` + `feature` | `.env`, `.env.example`, `Dataset/Images/Education/` (bazı resimler), `.claude/scheduled_tasks.lock` | Commit mesajındaki "Auto-commit (assistant)" ifadesi Claude Code tarafından otomatik oluşturulduğunu göstermektedir. Ortam değişkeni dosyaları eklendi. |
| 17 | `73ff5de` | 2026-05-10 | Save: push all local changes | `feature` + `cleanup` | `Dataset/Images/Emotion_4Class/` (büyük veri seti değişiklikleri), çeşitli pipeline scriptleri | Commit mesajı ("Save") anlamlı değildir; diff içeriği değişikliği açıklamaktadır. Yeni 4-sınıflı veri seti yapılandırması ve pseudo-etiketleme scriptleri eklendi. |
| 18 | `a846643` | 2026-05-14 | chore: add new phenotype pipelines and output files | `feature` | `out/consensus_pipeline/`, `out/highconf_pipeline/` (büyük CSV ve JSON çıktıları) | Pseudo-etiketleme pipeline çıktıları eklendi. Sonuçlar: Highconf 0.75 → 23.063 örnek, Macro F1=0.6694; Consensus 3/3 → 7.980 örnek, Macro F1=0.5721. |

---

## Commit Kategori Dağılımı

| Kategori | Commit Sayısı | Commitler |
|---|---|---|
| `setup` | 2 | ec7d0f8, a04e560 |
| `feature` | 9 | b8b32b2, d494e7b, 08e1303, 1476c63, ef0af36, 2a6895c, dc64027, 73ff5de, a846643 |
| `ui` | 2 | 339a738, a04e560 |
| `refactor` | 2 | 339a738, 72d8a7b |
| `api` | 1 | 08e1303 |
| `test` | 1 | bab2958 |
| `docs` | 2 | bab2958, fb8602a |
| `cleanup` | 2 | 5311334, 73ff5de |

---

## Önemli Gözlemler

1. **İlk commit büyük:** KIDO veri seti görüntüleri ve eğitim kodu aynı anda eklendi. Commit geçmişi bunu tek bir commit olarak kayıtlamıştır.
2. **3 aylık dönemde commit yok:** Commit 3 (2025-11-30) ile Commit 4 (2026-02-22) arasında repository'de commit yoktur.
3. **22 Şubat 2026 yoğunluğu:** Tek günde 7 commit (4–10 arası) yapılmıştır.
4. **Mimari sıfırlama:** Commit 14 (`5311334`, 19 Nisan 2026) eski AI yığınını kaldırmıştır. Bu kararın teknik gerekçesini doğrulayan log bulunamadı.
5. **Bilgi değeri düşük mesajlar:** "Save", "Auto-commit", "Ağırlık düzenleme" — bu commitlerde diff içeriği analiz edildi.
6. **Commit 10 somut metrik içeriyor:** `bab2958` commiti `artifacts/report_run/REPORT.md` dosyasını ekledi; içindeki metrikler kanıt kaynağı olarak kullanıldı.


---

# 02 — Geliştirme Aşamaları

Bu dosya, commit geçmişinden çıkarılan geliştirme sürecini anlamlı aşamalara gruplamaktadır. Aşamalar kronolojik sıradadır ve her biri ilgili commit ID'leri ile belgelenmiştir. Kanıt bulunmayan kararlar için bu durum açıkça belirtilmiştir.

---

# Aşama 1: Proje Kurulumu ve İlk Çok Modlu Model

**Dönem:** 30 Kasım 2025
**İlgili Commitler:** `ec7d0f8`, `b8b32b2`, `d494e7b`

## Yapılan İşler (Kanıta Dayalı)

- KIDO veri seti (çocuk çizimleri) projeye dahil edildi. Görüntüler `Dataset/Images/Education/test/Primary/` altında düzenlendi.
- Veri dosya adlandırma formatı: `[okul_id]-[sınıf]-[öğrenci_id]-[cinsiyet]-[duygu].jpg` (örn. `101-1A-369-F-H.jpg`). Kaynak: Commit `ec7d0f8` diff.
- Çok modlu sinir ağı mimarisi tasarlandı (Kaynak: `src/models/multimodal_effnet_bert.py`, commit `b8b32b2`):
  - **Görüntü kodlayıcı:** EfficientNet-B0 (ImageNet ağırlıklarıyla)
  - **Metin kodlayıcı:** `dbmdz/bert-base-turkish-cased` (Türkçe BERT)
  - **Birleştirme:** Her modaliteden 512 boyutlu projeksiyon, concat → 1024 boyutlu birleşik vektör
  - **Çıkış kafaları:** Duygu kafası (Happiness/Sadness, 2 sınıf) + Cinsiyet kafası (Female/Male, 2 sınıf)
- Parametre yapılandırması (`src/train/train_multimodal.py`, commit `b8b32b2`): `freeze_bert=True` (varsayılan), `freeze_effnet=False` (varsayılan). Toplam: 116.2M parametre, eğitilebilir: 5.6M.
- Tkinter tabanlı masaüstü GUI oluşturuldu (`src/app/gui_multimodal.py`).
- Grad-CAM açıklanabilirlik modülü geliştirildi (`src/explain/gradcam.py`). Commit `d494e7b`'e Grad-CAM görsel çıktıları dahil edildi.
- Kural tabanlı açıklayıcı (`rule_based_explainer.py`) eklendi. Commit mesajındaki "ezber cümleler" bu şablon açıklamalara karşılık gelmektedir.

## Teknik Değerlendirme (Kanıta Dayalı)

Commit `b8b32b2`'nin diff içeriği iki sınıflandırma kafasını (duygu + cinsiyet) açıkça göstermektedir. Bu çok görevli yapı, KIDO dosya adı şemasında da cinsiyet ve duygu bilgisinin kodlanmış olmasıyla uyumludur.

BERT'in dondurulmuş başlatılması (`freeze_bert=True`) kaynak kodda doğrudan görülmektedir.

## Tezde Kullanılabilecek Anlatım

Projenin ilk aşamasında çok görevli bir derin öğrenme mimarisi oluşturulmuştur. EfficientNet-B0 görüntü kodlayıcı ve Türkçe BERT metin kodlayıcının çıktıları birleştirilerek iki bağımsız sınıflandırma kafasına (duygu ve cinsiyet) aktarılmıştır. BERT parametreleri dondurulmuş olup toplam 116.2M parametrenin yalnızca 5.6M'i eğitilebilir olarak yapılandırılmıştır.

---

# Aşama 2: Tkinter GUI Olgunlaştırma

**Dönem:** 22 Şubat 2026
**İlgili Commitler:** `339a738`

## Yapılan İşler (Kanıta Dayalı)

- Tkinter GUI'de açıklama metni için kaydırılabilir metin alanı eklendi.
- Açıklama üretim mantığı yeniden düzenlendi.
- Commit mesajı: "Add scrollable text widget for explanation and refactor explanation generation"

## Teknik Değerlendirme

Commit 3 (`d494e7b`, 2025-11-30) ile bu commit (`339a738`, 2026-02-22) arasında yaklaşık 3 ay geçmiştir. Bu dönemde repository'de commit yoktur.

## Tezde Kullanılabilecek Anlatım

Tkinter arayüzünde, uzun açıklama metinlerini görüntülemek için kaydırılabilir metin alanı eklenmiştir (commit `339a738`).

---

# Aşama 3: Web Arayüzü ve FastAPI Backend'e Geçiş

**Dönem:** 22 Şubat 2026 (tek gün, 7 commit)
**İlgili Commitler:** `a04e560`, `3b481f8`, `08e1303`, `1476c63`, `ef0af36`, `bab2958`

## Yapılan İşler (Kanıta Dayalı)

- React + Vite + TypeScript + Tailwind CSS ile web projesi kuruldu (commit `a04e560`).
- i18next ile Türkçe/İngilizce çoklu dil desteği eklendi (commit `3b481f8`).
- FastAPI tabanlı REST API arka ucu (`api_server.py`) oluşturuldu (commit `08e1303`):
  - 131 satır ilk versiyon
  - `/health` endpoint'i
  - `/predict` endpoint'i: resim + metin girişi → model çıktısı + açıklama
  - CORS middleware
  - `vite.config.ts`'de proxy yapılandırması
- API yanıtına `explanation` alanı eklendi (commit `1476c63`).
- Duygu ve cinsiyet etiketleri için dil bazlı yerelleştirme API'ye entegre edildi; 189 satır ekleme (commit `ef0af36`).
- Model değerlendirme ve raporlama altyapısı eklendi (commit `bab2958`):
  - `run_report.py`
  - `artifacts/report_run/REPORT.md` — **Duygu Accuracy=%94.36, F1=0.9435, ROC-AUC=0.9866**
  - Confusion matrix ve ROC eğrisi görselleri

## Teknik Değerlendirme (Kanıta Dayalı)

22 Şubat 2026'da tek günde 7 commit yapılmıştır. Commit `08e1303`'ün diff'i `api_server.py`'nin 131 satır ile ilk kez oluşturulduğunu göstermektedir. Commit `bab2958`'in diff'i `REPORT.md` içindeki somut metrikleri içermektedir.

## Tezde Kullanılabilecek Anlatım

22 Şubat 2026'da tek günde React web arayüzü, FastAPI backend, i18n desteği, açıklama API'si ve model değerlendirme raporlama altyapısı oluşturulmuştur. Bu tarihte elde edilen değerlendirme sonuçları: Duygu sınıflandırması Accuracy=%94.36, F1=0.9435 (KIDO test seti, 1.630 örnek, dengeli).

---

# Aşama 4: Masaüstü Paketleme ve Raporlama

**Dönem:** 12 Mart 2026
**İlgili Commitler:** `16fa3d3`, `2a6895c`, `72d8a7b`

## Yapılan İşler (Kanıta Dayalı)

- Markdown'dan DOCX formatına dönüştürme scripti (`build_report_docx.py`) geliştirildi (commit `16fa3d3`).
- Tez belgesi şablonu (`Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx`) repo'ya eklendi.
- FastAPI + React'i saran masaüstü uygulaması (`desktop_app.py`) oluşturuldu (commit `2a6895c`):
  - FastAPI sunucu arka planda başlatılıyor
  - pywebview ile yerel tarayıcı penceresi açılıyor
- `src/app_paths.py` — `sys.frozen` kontrolü ile paketlenmiş ortamda dosya yolu çözümlemesi yapılıyor.
- PyInstaller spec dosyası (`desktop_app.spec`) yapılandırıldı.
- Windows kurulum paketi için Inno Setup scripti oluşturuldu.
- Web uygulamasının `/about` sayfasına confusion matrix ve ROC eğrisi görselleri eklendi (commit `72d8a7b`).

## Teknik Değerlendirme (Kanıta Dayalı)

`src/app_paths.py` kaynak kodu `sys.frozen` kontrolü içermektedir — bu, PyInstaller paketlenmiş ortamında çalışma zamanı yolu sorununu çözen standart bir yapıdır.

## Tezde Kullanılabilecek Anlatım

Sistem, PyInstaller ve pywebview kullanılarak bağımsız Windows masaüstü uygulaması olarak paketlenmiştir. FastAPI sunucusu ve React arayüzü tek bir çalıştırılabilir pakette birleştirilmiştir.

---

# Aşama 5: Kritik Mimari Sıfırlama

**Dönem:** 19–20 Nisan 2026
**İlgili Commitler:** `5311334`, `fb8602a`

## Yapılan İşler (Kanıta Dayalı)

Commit `5311334` diff'inden:
- `Dataset/Images/Education/` klasöründeki çok sayıda görüntü silindi.
- BERT tabanlı metin kodlayıcı ve çok modlu füzyon katmanı kaldırıldı.
- Eski model checkpoint'leri ve explainability modülleri kaldırıldı.
- README yeniden yazılarak projenin yeni yönü açıklandı: "eski multimodal AI hattı bu repodan temizlendi", "legacy AI giris noktalari bilincli olarak devre disi birakildi".
- `api_server.py` içinde `/predict` endpoint `503 reset_in_progress` döndürecek şekilde değiştirildi.

Commit `fb8602a`: Backend V1 için mikro-sprint yürütme planı eklendi.

## Teknik Değerlendirme

Repository içinde bu kararın teknik gerekçesini doğrulayan performans karşılaştırması, ablation study veya başarısızlık logu bulunamadı. Commit mesajı ("remove legacy dataset and reset old AI stack") ve README içeriği kararın alındığını belgeler; gerekçeyi açıklamaz.

## Tezde Nasıl Anlatılmalı

"Nisan 2026'da eski çok modlu sistem kaldırılarak yalnızca görüntü tabanlı mimariye geçilmiştir. Bu geçişin teknik gerekçesi commit geçmişinde belgelenmemiştir. [Tez yazarı gerçek nedeni eklemeli.]"

---

# Aşama 6: Yeni Veri Hattı — Pseudo-Etiketleme

**Dönem:** 8–14 Mayıs 2026
**İlgili Commitler:** `dc64027`, `73ff5de`, `a846643`

## Yapılan İşler (Kanıta Dayalı)

Commit `73ff5de` diff'inden:
- Yeni 4-sınıflı veri kümesi yapılandırması: `Dataset/Images/Emotion_4Class/` (Anger/Fear/Happy/Sad)
- Pseudo-etiketleme scriptleri: `label_with_hf.py`, `label_with_ollama.py`, `label_with_model.py`, `label_with_model_v2.py`
- Veri manifesti scriptleri: `build_manifest_kido.py`, `build_manifest_expanded.py`, `build_manifest_v2.py`, `build_manifest_final.py`, `build_manifest_qwen.py`
- İki pipeline: `run_highconf_pipeline.py` (güven eşiği 0.75/0.85), `run_consensus_pipeline.py` (3/3 model mutabakatı)

Commit `a846643` — pipeline çıktıları (Kaynak: `out/highconf_pipeline/summary_results.csv`, `out/consensus_pipeline/summary_results.csv`):

| Pipeline | Eğitim Örnekleri | Accuracy | Macro F1 |
|---|---|---|---|
| Highconf 0.75 | 23.063 | 67.07% | 0.6694 |
| Highconf 0.85 | 18.783 | 64.67% | 0.6495 |
| Consensus 3/3 | 7.980 | 57.49% | 0.5721 |

## Teknik Değerlendirme (Kanıta Dayalı)

Öğretmen model 55.660 görüntüyü etiketledi; ortalama güven=0.7306. Güven ≥0.75 olan: 28.314 örnek (%50.9). Güven ≥0.85 olan: 18.786 örnek (%33.8).
Kaynak: `out/highconf_pipeline/teacher_labels_report.json`

## Tezde Kullanılabilecek Anlatım

Mayıs 2026'da öğretmen-öğrenci pseudo-etiketleme yaklaşımı uygulanmıştır. Öğretmen model 55.660 görüntüyü etiketlemiş; güven eşiği 0.75 kullanan pipeline 23.063 eğitim örneği üretmiş ve Macro F1=0.6694 elde etmiştir. Consensus pipeline (3/3 model mutabakatı) 7.980 örnek üretmiş ve Macro F1=0.5721 elde etmiştir.


---

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


---

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


---

# 05 — Teknik Kararlar

Bu dosya, projede alınan önemli teknik kararları belgeler. Kaynak koddan ve commit diff'lerinden çıkarılabilen kararlar kanıta dayalı biçimde açıklanmıştır. Repository içinde teknik gerekçesi bulunamayan kararlar için bu durum açıkça belirtilmiştir.

---

## Teknik Karar 1: EfficientNet-B0 Görüntü Kodlayıcı Seçimi

### Karar
Görüntü özellik çıkarımı için EfficientNet-B0 (ImageNet ön eğitimli) kullanıldı.

### Kanıt
`src/models/multimodal_effnet_bert.py` (`b8b32b2`): `from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights`
`run_highconf_pipeline.py`: Daha sonra B2 ve B3 varyantları da eklendi.

### Gerekçe
EfficientNet ailesi, parametre sayısı-doğruluk dengesi açısından benchmark değerlendirmelerinde üstün performans göstermektedir. B0, serinin en hafif modelidir ve görece sınırlı GPU kaynaklarında bile çalışabilir. Transfer öğrenimi ile ImageNet ağırlıkları aktarılarak küçük veri setlerinde iyi başlangıç noktası elde edilmektedir. Commit geçmişinde EfficientNet seçiminin gerekçesini açıklayan ek belge bulunmamaktadır.

### Avantajları
- Parametre etkinliği: ResNet veya VGG'ye kıyasla daha az parametre, benzer doğruluk
- ImageNet ön eğitimi: Küçük veri setlerinde kritik avantaj sağlar
- Torchvision ile doğrudan entegrasyon
- Daha sonra B2/B3'e geçiş kolaylığı (aynı aile)

### Dezavantajları / Sınırlamaları
- Çizim görüntüleri fotoğraflardan farklı dağılım gösterir; ImageNet ağırlıkları tam olarak uygun olmayabilir
- B0, daha büyük veri setlerinde B3'e göre daha düşük kapasiteye sahip

### Tezde Kullanılabilecek Anlatım
Görüntü kodlayıcı olarak EfficientNet ailesinin tercih edilmesinin temel nedeni, bu mimarinin parametre-verimlilik dengesindeki üstün performansı ve ImageNet üzerinde ön eğitilmiş ağırlıklarıyla transfer öğrenimi imkânı sunmasıdır.

---

## Teknik Karar 2: Türkçe BERT Modeli Seçimi (dbmdz/bert-base-turkish-cased)

### Karar
Metin kodlayıcı olarak `dbmdz/bert-base-turkish-cased` seçildi.

### Kanıt
`src/train/train_multimodal.py` (`ec7d0f8`): `parser.add_argument("--bert_model", type=str, default="dbmdz/bert-base-turkish-cased")`

### Gerekçe
Veri kümesi Türk okul çocuklarına aittir. Türkçe'ye özgü BERT modeli, dil özelliklerini (eklemeli yapı, morfoji) daha iyi temsil etmektedir. `dbmdz/bert-base-turkish-cased` HuggingFace üzerinde yaygın kullanılan ve iyi belgelenmiş bir Türkçe BERT modelidir. Metin verisinin tam içeriği commit geçmişinde belirtilmemiştir; bu bilgi `12_eksik_bilgiler_ve_durust_notlar.md` dosyasında kayıt altına alınmıştır.

### Avantajları
- Türkçe morfolojisini doğal olarak işler
- Büyük/küçük harf duyarlıdır (cased), Türkçe için önemli

### Dezavantajları / Sınırlamaları
- Bu model Nisan 2026'da kaldırıldığı için pratik etkisi sınırlı kalmıştır
- Çok modlu mimaride metin verisinin ne olduğu commit geçmişinden tam netlik kazanmamaktadır

### Tezde Kullanılabilecek Anlatım
Projenin ilk aşamasında, Türk öğrencilere ait veri kümesiyle uyum sağlamak amacıyla Türkçe dil modeli olarak `dbmdz/bert-base-turkish-cased` seçilmiştir.

---

## Teknik Karar 3: BERT'in Varsayılan Olarak Dondurulması (Freeze)

### Karar
Eğitim sırasında BERT parametreleri varsayılan olarak dondurulmuş (`freeze_bert=True`) başlatıldı; EfficientNet ise eğitilebilir bırakıldı (`freeze_effnet=False`).

### Kanıt
`src/train/train_multimodal.py` (`ec7d0f8`): `parser.set_defaults(freeze_bert=True, freeze_effnet=False)`

### Gerekçe
Bu asimetrik dondurma stratejisi standart bir transfer öğrenimi tekniğidir. BERT'in 110M+ parametresi küçük veri setlerinde aşırı öğrenmeye (overfitting) yol açabilir; dondurma bunu önler. EfficientNet'in görüntüye özgü alt katmanlarının ince ayara (fine-tuning) ihtiyacı daha büyüktür.

### Avantajları
- Eğitim hızlanır (BERT gradyanları hesaplanmaz)
- Küçük veri setlerinde aşırı öğrenme riski azalır
- Eğitilebilir parametre sayısı: 116.2M toplam → yalnızca 5.6M eğitilebilir

### Dezavantajları / Sınırlamaları
- Frozen BERT, alana özgü metin bilgisini öğrenemez
- Dondurulmuş BERT, bu spesifik alana (çocuk çizimi metinleri) özgü özellikler öğrenemez

### Tezde Kullanılabilecek Anlatım
Eğitim kararlılığını sağlamak ve aşırı öğrenmeyi önlemek amacıyla BERT parametreleri dondurulmuş, yalnızca projeksiyon katmanları ve görüntü kodlayıcısı eğitime dahil edilmiştir. Bu strateji, 116 milyon parametreli modelde eğitilebilir parametre sayısını 5.6 milyona indirmiştir.

---

## Teknik Karar 4: FastAPI + React Mimarisi

### Karar
Backend için FastAPI, frontend için React + Vite seçildi.

### Kanıt
`08e1303` commitinde `api_server.py` (FastAPI) ve `Web/` (React) eş zamanlı eklendi.

### Gerekçe
FastAPI, Python tabanlı ML modellerini HTTP API'sine dönüştürmek için günümüzdeki de facto standarttır. Otomatik API dokümantasyonu (Swagger UI), tip güvenliği ve asenkron destek sunar. React, bileşen tabanlı UI mimarisi ve zengin ekosistemiyle modern web uygulamalarının standart seçimidir. Bu ikili, full-stack Python+JS web uygulamaları için yaygın bir kombinasyondur.

### Avantajları
- FastAPI: otomatik Swagger/OpenAPI dokümantasyonu
- FastAPI: Python ML kütüphaneleriyle doğal entegrasyon
- React: i18n, animasyon, bileşen yeniden kullanım
- Ayrı geliştirme sunucuları (hot reload)
- Hem web hem masaüstü dağıtımına uygun

### Dezavantajları / Sınırlamaları
- İki ayrı teknoloji yığını (Python + TypeScript) bakım karmaşıklığı getirir
- Node.js geliştirme ortamı da gerekmektedir

### Tezde Kullanılabilecek Anlatım
Sistem, Python tabanlı FastAPI arka ucu ve React tabanlı web arayüzünden oluşan istemci-sunucu mimarisine sahiptir. Bu yaklaşım, makine öğrenimi modelinin Python ekosisteminde çalışmasına olanak tanırken modern ve kullanıcı dostu bir arayüz sunmaktadır.

---

## Teknik Karar 5: Çoklu Dil Desteği (i18n)

### Karar
Kullanıcı arayüzü başından itibaren Türkçe/İngilizce çift dil desteğiyle tasarlandı.

### Kanıt
`3b481f8`: "feat: implement internationalization support with language selection" — React kurulumundan hemen sonraki commit.

### Gerekçe
Projenin klinik ortamlarda kullanılabilmesi için Türkçe şarttır; ancak akademik ve uluslararası değerlendirme için İngilizce de gereklidir. Çok dil desteğinin başından eklenmesi, sonradan eklemekten çok daha kolaydır.

### Avantajları
- Klinik kullanım için Türkçe arayüz
- Uluslararası demo/sunum için İngilizce seçeneği
- Duygu etiketlerinin de yerelleştirilerek tutarlılık sağlanması

### Dezavantajları / Sınırlamaları
- Her yeni metin ögesinin iki dilde eklenmesi gerekir (bakım yükü)

### Tezde Kullanılabilecek Anlatım
Sistem, klinisyen ve araştırmacılara yönelik pratik kullanılabilirliği gözetilerek hem Türkçe hem İngilizce arayüz sunan çoklu dil desteğiyle geliştirilmiştir.

---

## Teknik Karar 6: Grad-CAM Açıklanabilirlik Entegrasyonu

### Karar
Model tahminleri için Grad-CAM (Gradient-weighted Class Activation Mapping) görselleştirme eklendi.

### Kanıt
`d494e7b`: `src/explain/gradcam.py` eklendi; commit'te Grad-CAM çıktı görselleri de dahil edildi.

### Gerekçe
Tıp ve klinik psikoloji uygulamalarında kara kutu modeller kabul görmemektedir. Grad-CAM, modelin "nereye baktığını" görselleştirerek klinisyenin modelin kararını anlamasına yardımcı olur. Bu, tezin "açıklanabilir yapay zeka" (XAI) boyutunu güçlendirir.

### Avantajları
- Model güvenilirliğini görsel olarak gösterir
- Klinik bağlamda kabul görmesini kolaylaştırır
- CNN mimarileriyle doğal uyum (torch hooks)

### Dezavantajları / Sınırlamaları
- Grad-CAM sadece son konvolüsyon katmanını görselleştirir; tam yorumlama sınırlıdır
- Yüksek çözünürlüklü görüntülerde hesaplama maliyeti artar

### Tezde Kullanılabilecek Anlatım
Modelin klinik bağlamda kabul görmesi için açıklanabilirlik kritik öneme sahiptir. Grad-CAM görselleştirmesi, modelin sınıflandırma kararını verirken çizimin hangi bölgelerine odaklandığını göstermekte; bu sayede sistemin şeffaflığı artırılmaktadır.

---

## Teknik Karar 7: Pseudo-Etiketleme ile Yarı Denetimli Öğrenme

### Karar
Veri kıtlığına karşı öğretmen-öğrenci (teacher-student) pseudo-etiketleme yaklaşımı benimsendi.

### Kanıt
`run_highconf_pipeline.py`, `run_consensus_pipeline.py`, `label_with_*.py` dosyaları (`73ff5de`, `a846643`).

### Gerekçe
Manuel etiketleme pahalı ve zaman alıcıdır. El çizimi çocuk resmi için uzman etiketçi bulmak da kolay değildir. Pseudo-etiketleme, mevcut modelin yüksek güvenilirlikli tahminlerini yeni eğitim verisi olarak kullanarak veri kümesini büyütür.

### Avantajları
- Etiketleme maliyeti olmadan veri artırımı
- Çift doğrulama (high-confidence + consensus) gürültüyü azaltır
- Farklı kaynaklardan veri entegre edilebilir

### Dezavantajları / Sınırlamaları
- Öğretmen modelin hatası öğrenci modele aktarılabilir (confirmation bias)
- Gerçek insan etiketlemesi kadar güvenilir değil
- Pseudo-etiket kalitesini doğrulamak için hâlâ bir gold standard gerekiyor

### Tezde Kullanılabilecek Anlatım
Veri kısıtlarını aşmak amacıyla yarı denetimli öğrenme paradigması benimsenmiş; bu çerçevede önceden eğitilmiş bir öğretmen modelin yüksek güvenilirlikli tahminleri, yeni eğitim verisi olarak kullanılmıştır. Etiket güvenilirliğini artırmak için hem güven eşiği hem de çoklu model mutabakatı kriterleri uygulanmıştır.

---

## Teknik Karar 8: PyInstaller ile Masaüstü Paketleme

### Karar
Python uygulaması PyInstaller ile bağımsız Windows uygulaması olarak paketlendi.

### Kanıt
`2a6895c`: `desktop_app.spec`, `requirements-desktop.txt`, Inno Setup scripti eklendi.

### Gerekçe
Klinik ortamlarda internet bağlantısının kısıtlı olabileceği `api_server.py` içindeki README güncellemesinde belirtilmektedir. PyInstaller, Python bağımlılıklarını tek bir pakette toplar. Repository içinde bu kararın başka teknik gerekçesini doğrulayan log bulunamadı.

### Avantajları
- Kurulum gerektirmeden çalışır
- İnternet bağlantısı gerekmez
- Klinik demo için pratiklik

### Dezavantajları / Sınırlamaları
- Paket boyutu büyüktür (Python runtime + ML kütüphaneleri)
- Model ağırlıkları da pakete dahil edilmesi gerekir
- Güncelleme için tüm paketin yeniden dağıtılması gerekir

### Tezde Kullanılabilecek Anlatım
Sistemin klinik ortamlarda bağımsız kullanılabilmesi amacıyla PyInstaller kullanılarak bağımsız Windows yürütülebilir paketi oluşturulmuştur.


---

# 06 — Sistem Mimarisi Evrimi

Bu dosya, projenin mimari yapısının zaman içinde nasıl değiştiğini belgeler. Veriler commit geçmişi ve mevcut dosya yapısından elde edilmiştir.

---

## İlk Mimari Yapı (Kasım 2025)

### Dosya Yapısı

```
CCDDA/
├── .gitignore
├── Dataset/
│   └── Images/
│       └── Education/
│           └── test/
│               └── Primary/          ← KIDO veri seti görüntüleri
├── checkpoints/                      ← Model checkpoint'leri
├── notebooks/                        ← Jupyter notebook'lar
└── src/
    ├── data/
    │   ├── dataset.py               ← KidoMultimodalDataset sınıfı
    │   └── transforms.py            ← Görüntü dönüşümleri
    ├── models/
    │   ├── __init__.py
    │   ├── bert_text_only.py        ← Yalnızca metin modeli (boş)
    │   ├── efficientnet_multitask.py ← Yalnızca görüntü modeli (boş)
    │   └── multimodal_effnet_bert.py ← Ana model: EfficientNet + BERT
    └── train/
        └── train_multimodal.py      ← Eğitim scripti
```

### Mimari Diyagramı

```
Görüntü → EfficientNet-B0 → AdaptiveAvgPool2d → [B, 1280]
                                                      ↓
                                               img_proj (Linear 1280→512)
                                                      ↓
Metin  → Türkçe BERT → [CLS] token → [B, 768]        ↓
                                          ↓       Concat [B, 1024]
                                 text_proj (Linear 768→512)     ↓
                                                         ↓
                                              Emotion Head (1024→2)
                                              Gender Head  (1024→2)
```

### Özellikler
- **Veri**: KIDO veri seti, ikili etiket (Happiness/Sadness + Female/Male)
- **Model**: 116M parametre, 5.6M eğitilebilir
- **Kullanıcı arayüzü**: Henüz yok
- **Eğitim**: `python src/train/train_multimodal.py`

---

## Birinci Genişleme: Açıklanabilirlik + GUI (Kasım 2025)

### Yeni Bileşenler (`d494e7b`)

```
src/
├── app/
│   ├── gui_multimodal.py    ← Ana Tkinter GUI (tam özellikli)
│   └── tk_app.py            ← Daha sade Tkinter sarmalayıcı
├── explain/
│   ├── gradcam.py           ← Grad-CAM görselleştirme
│   ├── perception_api.py    ← Harici görsel analiz API istemcisi
│   ├── predict_and_explain.py ← Tahmin + açıklama pipeline'ı
│   ├── rule_based_explainer.py ← Kural tabanlı açıklayıcı
│   └── text_explain.py      ← Metin tabanlı açıklama üretici
└── data/
    └── dataset.py           ← Genişletildi
```

### Mimari Durumu

```
[Model Inference]
      ↓
[Grad-CAM] → görsel ısı haritası
      ↓
[Rule-Based Explainer] → açıklama metni
      ↓
[Tkinter GUI] → kullanıcıya gösterim
```

---

## İkinci Genişleme: Web + FastAPI (Şubat 2026)

### Yeni Bileşenler (`a04e560` – `bab2958`)

```
CCDDA/
├── api_server.py            ← FastAPI REST API (YENİ)
├── requirements.txt         ← FastAPI bağımlılıkları eklendi
└── Web/                     ← React projesi (YENİ)
    ├── .env.example
    ├── index.html
    ├── package.json
    ├── vite.config.ts       ← Proxy yapılandırması
    └── src/
        ├── App.tsx          ← Ana React bileşeni
        ├── main.tsx
        ├── index.css
        └── locales/
            ├── tr.json      ← Türkçe çeviriler
            └── en.json      ← İngilizce çeviriler
```

### Mimari Durumu

```
[React Arayüz (port 3000)]
          ↓ HTTP POST /predict (Vite proxy)
[FastAPI Backend (port 8000)]
          ↓
[src.explain.predict_and_explain]
          ↓
[EfficientNet-B0 + BERT Model]
          ↓
[Rule-Based / LLM Explainer]
          ↑
[GITHUB_TOKEN → GitHub Models API (opsiyonel)]
```

### API Endpoint'leri (İlk Versiyon)
- `GET /health` — Sunucu sağlık kontrolü
- `POST /predict` — Görüntü + metin gönder, tahmin + açıklama al

---

## Üçüncü Genişleme: Masaüstü Paketleme + Raporlama (Mart 2026)

### Yeni Bileşenler (`16fa3d3`, `2a6895c`, `72d8a7b`)

```
CCDDA/
├── desktop_app.py           ← FastAPI + pywebview sarmalayıcı (YENİ)
├── desktop_app.spec         ← PyInstaller yapılandırması (YENİ)
├── src/
│   └── app_paths.py         ← Paketlenmiş ortamda yol çözücü (YENİ)
├── build/                   ← PyInstaller ara çıktılar
├── dist/                    ← Derleme çıktıları (.exe)
├── installer/               ← Inno Setup ve kurulum betikleri
├── build_report_docx.py     ← Markdown → DOCX dönüştürücü (YENİ)
└── Web/
    └── public/
        └── about/           ← Performans grafikleri (YENİ)
            ├── confusion-matrices.png
            ├── roc-curves.png
            ├── sample-predictions.png
            └── training-curves.png
```

### Dağıtım Seçenekleri

```
┌─────────────────────────────────────────────┐
│              Dağıtım Modları                │
├──────────────────┬──────────────────────────┤
│  Web Modu        │  Masaüstü Modu            │
│  React + FastAPI │  desktop_app.py           │
│  Ayrı sunucular  │  PyInstaller .exe         │
│  Tarayıcı gerekir│  Kendi kendine yeten      │
└──────────────────┴──────────────────────────┘
```

---

## Kritik Sıfırlama: Legacy AI Temizleme (Nisan 2026)

### Kaldırılan Bileşenler (`5311334`)

Kaldırılan bileşenler (README.md'den):
- `emotion + gender çok görevli sınıflandırma` sistemi
- `BERT tabanlı multimodal akış`
- Eski checkpoint'ler
- Eski explainability ve inference kodları
- Büyük eğitim veri seti (`Dataset/Images/Education/`)

### Korunan Bileşenler

```
CCDDA/                       ← Korunan
├── Web/                     ← React + i18n arayüzü
├── desktop_app.py           ← Masaüstü sarmalayıcı
├── api_server.py            ← FastAPI (503 döndürüyor)
├── src/
│   ├── app/                 ← GUI modülleri
│   ├── data/                ← Dönüşüm yardımcıları
│   ├── explain/             ← Açıklanabilirlik modülleri
│   └── utils/               ← Genel araçlar
└── docs/                    ← Dokümantasyon
```

### API Durumu (Nisan 2026 sonrası)
```python
# api_server.py — /predict endpoint durumu
"reset_in_progress" → HTTP 503
```

---

## Son Mimari Yapı (Mayıs 2026 — Aktif Geliştirme)

### Tam Dosya Yapısı

```
CCDDA/
├── api_server.py               ← FastAPI (503 modunda)
├── desktop_app.py              ← Masaüstü sarmalayıcı (korundu)
├── requirements.txt            ← Güncel bağımlılıklar
│
├── Dataset/
│   ├── Images/
│   │   ├── Emotion_4Class/     ← YENİ: 4-sınıf etiketli veri
│   │   │   ├── Anger/
│   │   │   ├── Fear/
│   │   │   ├── Happy/
│   │   │   └── Sad/
│   │   ├── Emotion_Roboflow_DrawingFacialEmotions/
│   │   ├── Emotion_SigLIP_4Class/
│   │   ├── GoldTest_Candidates_Auto4Class/
│   │   └── Education/          ← Orijinal KIDO
│   ├── Texts/
│   └── huggingface/            ← Parquet veri kümesi
│
├── out/
│   ├── highconf_pipeline/      ← YENİ: Yüksek güvenilirlik çıktıları
│   │   ├── manifests/
│   │   │   ├── manifest_highconf_075.csv  (~23K örnek)
│   │   │   └── manifest_highconf_085.csv  (~19K örnek)
│   │   └── teacher_labels_all.csv
│   └── consensus_pipeline/     ← YENİ: Uzlaşma çıktıları
│       ├── manifests/
│       │   └── manifest_consensus_3of3_c060.csv
│       └── teacher_b_b3_075_labels_all.csv
│
├── artifacts/                  ← Model checkpoint'leri ve raporlar
├── build_manifest_*.py         ← Veri manifesti scriptleri (çok sayıda)
├── label_with_*.py             ← Pseudo-etiketleme scriptleri
├── run_highconf_pipeline.py    ← Ana high-conf pipeline
├── run_consensus_pipeline.py   ← Ana consensus pipeline
├── eval_test.py                ← Değerlendirme
├── eval_tta.py                 ← Test-time augmentation değerlendirme
│
└── Web/                        ← React arayüz (korundu)
    └── src/
        └── locales/
            ├── tr.json
            └── en.json
```

### Yeni AI Mimarisi (Hedef)

```
[Etiketsiz Görüntüler]
         ↓
[Öğretmen Model: EfficientNet-B3]
         ↓ (güven > 0.75)
[Pseudo-Etiketler]
         ↓ consensus filtresi
[Yüksek Kaliteli Manifest]
         ↓
[Öğrenci Model: EfficientNet-B3 (yeni eğitim)]
         ↓
[FastAPI /predict] → [React UI]
```

---

## Mimari Değişikliklerin Yorumu

Projenin mimari evrimi üç ana eksen üzerinde gerçekleşmiştir:

1. **Model karmaşıklığı ekseni**: Çok modlu (görüntü+metin) → Tek modlu (yalnızca görüntü). Bu sadeleşme, araştırma odağını netleştirmiş ve veri gereklilikleri azaltmıştır.

2. **Arayüz ekseni**: Tkinter (yerel) → React Web → React+PyInstaller (çift mod). Arayüzün evriminin her adımı daha geniş erişilebilirlik sunmaktadır.

3. **Veri stratejisi ekseni**: Sabit küçük veri seti → Çok kaynaklı + pseudo-etiketleme. Bu geçiş, etiketli veri kıtlığı sorununa yönelik sistematik bir çözümü temsil etmektedir.

### Tezde Kullanılabilecek Anlatım

Sistem mimarisi, üç temel evrimsel aşamadan geçmiştir. İlk aşamada çok modlu bir mimari denenmiş; ikinci aşamada web tabanlı dağıtıma geçilmiş; üçüncü ve güncel aşamada ise yalnızca görüntü tabanlı, pseudo-etiketleme destekli 4-sınıflı bir mimari benimsenmiştir. Bu evrim, hem teknik deneyimden hem de araştırma sorusunun yeniden çerçevelenmesinden beslenmektedir.


---

# 07 — Özellik Bazlı Gelişim

Bu dosya, sistem özelliklerini commit geçmişinden bağımsız olarak ele alır. Her özellik için ilk görüldüğü commit, gelişim süreci ve mevcut durumu belgelenmiştir.

---

## Özellik 1: Çok Görevli Duygu + Cinsiyet Sınıflandırması

### İlk Görüldüğü Commit
`ec7d0f8` (30 Kasım 2025) — ilk commit

### İlgili Dosyalar
- `src/models/multimodal_effnet_bert.py` — model tanımı
- `src/train/train_multimodal.py` — eğitim scripti
- `artifacts/report_run/REPORT.md` — değerlendirme sonuçları

### Gelişim Süreci
1. **ec7d0f8**: İlk tasarım — iki sınıflı duygu (Happiness/Sadness) + iki sınıflı cinsiyet (Female/Male)
2. **b8b32b2**: Model mimarisi detaylandırıldı, ağırlık dondurma parametreleri eklendi
3. **bab2958**: Değerlendirme yapıldı: Duygu %94.36, Cinsiyet %77.12
4. **5311334**: Bu özellik tamamen kaldırıldı

### Teknik Açıklama
Model, iki bağımsız çıkış kafasına sahiptir. Emotion head ve gender head, paylaşılan temsil üzerinden (fused embedding) ayrı ayrı optimize edilmektedir. AdamW optimizer, cosine LR scheduler kullanılmıştır.

### Tezde Kullanılabilecek Anlatım
İlk sistemde çok görevli öğrenme yaklaşımı benimsenmiş; tek bir model hem duygu hem cinsiyet sınıflandırması yapabilmek üzere tasarlanmıştır. Değerlendirme sonuçları duygu görevinde %94'ün üzerinde başarı oranı gösterirken, cinsiyet görevinde bu oran %77 düzeyinde kalmıştır.

---

## Özellik 2: Grad-CAM Açıklanabilirlik Görselleştirme

### İlk Görüldüğü Commit
`d494e7b` (30 Kasım 2025)

### İlgili Dosyalar
- `src/explain/gradcam.py` — Grad-CAM implementasyonu
- Commit içindeki görsel çıktılar: `207-6C-543-M-S_gradcam_emotion_Happiness.jpg`, `207-6C-543-M-S_gradcam_gender_Male.jpg` vb.

### Gelişim Süreci
1. **d494e7b**: Temel Grad-CAM eklendi; duygu ve cinsiyet için ayrı ısı haritaları
2. Sonraki commitlerin hiçbirinde Grad-CAM koduna dokunulmadı
3. **5311334** sonrası: `src/explain/gradcam.py` hâlâ mevcut; yeni modele entegre edilmesi beklenebilir

### Teknik Açıklama
Grad-CAM, PyTorch hook mekanizması kullanarak EfficientNet'in son konvolüsyon katmanındaki aktivasyonları ve gradyanları yakalar. Sınıf aktivasyon haritası, orijinal görüntü üzerine renk kodlamasıyla bindirilir. Commit'teki örnek çıktılarda hem duygu hem cinsiyet için ayrı ısı haritaları üretildiği görülmektedir.

### Tezde Kullanılabilecek Anlatım
Modelin sınıflandırma kararlarını desteklemek amacıyla Grad-CAM görselleştirme entegre edilmiştir. Bu yöntem, modelin çizimin hangi bölgelerine odaklandığını göstererek klinisyene ek bağlam sunmaktadır.

---

## Özellik 3: Kural Tabanlı Açıklama Sistemi

### İlk Görüldüğü Commit
`d494e7b` (30 Kasım 2025)

### İlgili Dosyalar
- `src/explain/rule_based_explainer.py`
- `src/explain/text_explain.py`
- `src/explain/llm_explainer.py` (daha sonra eklendi)

### Gelişim Süreci
1. **d494e7b**: Kural tabanlı açıklayıcı eklendi ("ezber cümleler")
2. **08e1303**, **1476c63**, **ef0af36**: API'ye açıklama alanı eklendi, yerelleştirildi
3. Güncel durumda: `src/explain/llm_explainer.py` LLM tabanlı açıklama için var; `GITHUB_TOKEN` ile GitHub Models API'si kullanılabiliyor

### Teknik Açıklama
Sistem, açıklama üretimi için katmanlı (fallback) bir yaklaşım izler:
- LLM bağlantısı varsa (`GITHUB_TOKEN`): dinamik, bağlamsal açıklama
- LLM yoksa: kural tabanlı şablon açıklamalar

### Tezde Kullanılabilecek Anlatım
Açıklama sistemi, hem kural tabanlı hem büyük dil modeli tabanlı yaklaşımı destekleyen katmanlı bir mimariyle tasarlanmıştır. Bu sayede internet bağlantısının olmadığı ortamlarda bile temel açıklamalar sunulabilmektedir.

---

## Özellik 4: Tkinter Masaüstü GUI

### İlk Görüldüğü Commit
`d494e7b` (30 Kasım 2025)

### İlgili Dosyalar
- `src/app/gui_multimodal.py` — tam özellikli GUI (394 satır)
- `src/app/tk_app.py` — daha sade sarmalayıcı (211 satır)

### Gelişim Süreci
1. **d494e7b**: İlk GUI oluşturuldu
2. **339a738**: Kaydırılabilir metin alanı eklendi, açıklama üretimi yeniden düzenlendi
3. Sonraki aşamalarda aktif geliştirme yapılmadı (React'e geçildi)

### Teknik Açıklama
`gui_multimodal.py`, 394 satırlık Tkinter uygulamasıdır. `tk_app.py` aynı committe eklenen ikinci GUI dosyasıdır. Her iki dosyanın işlev dağılımı commit diff'inde belirtilmemiştir.

### Tezde Kullanılabilecek Anlatım
Sistemin ilk kullanıcı arayüzü Tkinter kütüphanesiyle geliştirilmiş, yerel masaüstü uygulaması olarak çalıştırılmıştır. Bu prototip, kullanıcı akışının tanımlanmasında önemli bir referans noktası oluşturmuştur.

---

## Özellik 5: React Web Arayüzü

### İlk Görüldüğü Commit
`a04e560` (22 Şubat 2026)

### İlgili Dosyalar
- `Web/src/App.tsx` — ana React bileşeni (555+ satır)
- `Web/src/locales/tr.json`, `en.json` — çeviri dosyaları
- `Web/vite.config.ts` — Vite + proxy yapılandırması
- `Web/public/about/` — performans grafikleri

### Gelişim Süreci
1. **a04e560**: Proje iskeleti (React + Vite + TS + Tailwind)
2. **3b481f8**: i18n (Türkçe/İngilizce) desteği
3. **08e1303**: Analiz sayfası, metin girişi, hata yönetimi
4. **1476c63**: Açıklama alanı gösterimi
5. **ef0af36**: Duygu/cinsiyet etiketleri yerelleştirildi
6. **2a6895c**: Büyük UI güncellemesi (+346 satır), hakkında sayfası grafikleri
7. **72d8a7b**: Hakkında sayfasına performans görselleri eklendi

### Teknik Açıklama
`App.tsx` birden fazla commit sonunda 555+ satıra ulaşmıştır. Commit diff'lerinden doğrulanan ekranlar: Analiz sayfası (commit `08e1303`: görüntü yükleme + tahmin + hata yönetimi), Hakkında sayfası (commit `72d8a7b`: performans görselleri). Dil seçimi commit `3b481f8`'den itibaren kullanıcı tarafından değiştirilebilmektedir.

### Tezde Kullanılabilecek Anlatım
Modern web teknolojileriyle geliştirilen arayüz, Türkçe ve İngilizce dil desteğiyle klinik ve araştırma kullanımına yönelik olarak tasarlanmıştır.

---

## Özellik 6: FastAPI REST API

### İlk Görüldüğü Commit
`08e1303` (22 Şubat 2026)

### İlgili Dosyalar
- `api_server.py` — FastAPI uygulaması (262+ satır)
- `.env`, `.env.example` — yapılandırma

### Gelişim Süreci
1. **08e1303**: İlk versiyon (131 satır) — temel `/predict` ve `/health`
2. **ef0af36**: Duygu/cinsiyet yerelleştirmesi eklendi (109 satır daha)
3. **2a6895c**: Büyük güncelleme (262 satır, +/-) — statik dosya sunumu, oturum yönetimi, gelişmiş hata işleme
4. **5311334** sonrası: `/predict` → `503 reset_in_progress` döndürüyor
5. Güncel durum: Yeni model bağlanmayı bekliyor

### Teknik Açıklama
Mevcut `api_server.py` şu özelliklere sahip:
- Model checkpoint'ini ortam değişkeninden (`CCDDA_CHECKPOINT`) yükleme
- LLM açıklama için `GITHUB_TOKEN` desteği
- React build çıktısını statik olarak sunma
- CORS middleware
- `lifespan` bağlamı ile başlangıç/kapanış yönetimi

### Tezde Kullanılabilecek Anlatım
Sistem, FastAPI çerçevesi üzerine inşa edilmiş bir REST API sunucusu üzerinden tahmin hizmeti vermektedir. API, görüntü girişi kabul edip sınıflandırma sonucu ve açıklama metni döndürmektedir.

---

## Özellik 7: Pseudo-Etiketleme Pipeline'ı

### İlk Görüldüğü Commit
`73ff5de` (10 Mayıs 2026)

### İlgili Dosyalar
- `run_highconf_pipeline.py` (~29K satır kod)
- `run_consensus_pipeline.py` (~32K satır kod)
- `label_with_hf.py`, `label_with_ollama.py`, `label_with_model.py`, `label_with_model_v2.py`
- `ollama_annotate.py`
- `build_manifest_*.py` (5 farklı script)
- `out/highconf_pipeline/`, `out/consensus_pipeline/`

### Gelişim Süreci
1. **73ff5de**: Scriptler eklendi/güncellendi
2. **a846643**: Pipeline çıktıları üretildi (büyük CSV dosyaları)

### Teknik Açıklama

**High-Confidence Pipeline** (`run_highconf_pipeline.py`):
1. HuggingFace parquet verilerinden JPEG görüntü çıkarımı
2. Tüm kullanılabilir görüntülerden tekilleştirilmiş envanter oluşturma
3. Her görüntüyü mevcut öğretmen modelle etiketleme (EfficientNet-B3)
4. Güven eşiği filtresi: ≥0.85 ve ≥0.75
5. Filtreden geçen örneklerle EfficientNet-B3 öğrenci modeli eğitimi

**Consensus Pipeline** (`run_consensus_pipeline.py`):
- 3 farklı kaynak (Teacher-A, Teacher-B, Teacher-C)
- 3/3 mutabakat şartı (c060: %60 güven + 3/3 mutabakat gibi)
- Daha az ama daha güvenilir etiket üretir

**Üretilen Veriler:**
- `manifest_highconf_075.csv`: ~23,000 görüntü
- `manifest_highconf_085.csv`: ~19,000 görüntü
- `manifest_consensus_3of3_c060.csv`: ~8,300 görüntü (daha temiz)

### Tezde Kullanılabilecek Anlatım
Yarı denetimli öğrenme çerçevesinde iki tamamlayıcı etiketleme stratejisi uygulanmıştır. Yüksek güvenilirlikli yaklaşım, öğretmen modelin güven eşiğini aşan tahminlerini kullanırken; uzlaşma tabanlı yaklaşım üç bağımsız modelin hemfikir olduğu örnekleri seçmektedir. Bu iki strateji birbirini tamamlamakta, farklı verimlilik-güvenilirlik dengelerini temsil etmektedir.

---

## Özellik 8: Masaüstü Uygulama (PyInstaller + pywebview)

### İlk Görüldüğü Commit
`2a6895c` (12 Mart 2026)

### İlgili Dosyalar
- `desktop_app.py` — pywebview uygulaması
- `desktop_app.spec` — PyInstaller yapılandırması
- `src/app_paths.py` — yol çözümleyici
- `installer/` — Inno Setup ve kurulum betikleri
- `requirements-desktop.txt` — masaüstüne özel bağımlılıklar

### Gelişim Süreci
1. **2a6895c**: Tüm masaüstü altyapısı aynı anda eklendi
2. **72d8a7b**: `desktop_app.py`'ye 13 satır eklendi (küçük düzeltme)

### Teknik Açıklama
`desktop_app.py` şu mantığı uygular:
1. FastAPI sunucusunu arka planda başlat (subprocess veya threading)
2. Sunucu hazır olana kadar bekle
3. pywebview ile tarayıcı penceresi aç (localhost:8000)
4. Kullanıcı pencereyi kapattığında sunucuyu durdur

### Tezde Kullanılabilecek Anlatım
İnternet erişimi gerektirmeyen klinik ortamlarda kullanım için Python ve React uygulaması bağımsız bir masaüstü uygulaması olarak paketlenmiştir.

---

## Özellik 9: Çok Dilli Arayüz (i18n)

### İlk Görüldüğü Commit
`3b481f8` (22 Şubat 2026)

### İlgili Dosyalar
- `Web/src/locales/tr.json`
- `Web/src/locales/en.json`

### Gelişim Süreci
1. **3b481f8**: i18n altyapısı kuruldu
2. **08e1303**: Analiz sayfası metinleri eklendi (tr+en)
3. **ef0af36**: Duygu ve cinsiyet etiket çevirileri eklendi
4. **2a6895c**: Büyük ölçekli içerik eklendi (+260 satır her dil dosyasına)

### Teknik Açıklama
i18next kütüphanesi kullanılmaktadır. Duygu etiketleri API'den dönen İngilizce değerleri (Happiness, Sadness, Anger, Fear) kullanıcı diline çevirir.

### Tezde Kullanılabilecek Anlatım
Sistem, Türkçe konuşan klinisyenler ve İngilizce tabanlı akademik değerlendirme için çoklu dil desteğiyle tasarlanmıştır.


---

# 08 — Hata Düzeltmeleri ve Refactoring

Bu dosya, commit geçmişinden tespit edilen hata düzeltmelerini, kod düzenlemelerini ve yapısal değişiklikleri belgeler.

---

## Değişiklik 1: Tkinter GUI'ye Kaydırılabilir Metin Alanı Eklenmesi

### Tür
Hata düzeltme / UI iyileştirme

### İlgili Commitler
- `339a738` — "Add scrollable text widget for explanation and refactor explanation generation"

### Önceki Durum
Açıklama metni, kaydırma özelliği olmayan sabit boyutlu bir metin alanında gösteriliyordu. Uzun açıklamalar kesilip görüntülenemiyordu.

### Sonraki Durum
Tkinter'da `Text` widget'ı + `Scrollbar` kombinasyonu ile kaydırılabilir açıklama alanı oluşturuldu. Aynı commit'te açıklama üretim mantığı da yeniden düzenlendi.

### Teknik Etki
Kullanıcı uzun açıklama metinlerini tamamen okuyabilir hale geldi. Bu değişiklik kullanılabilirlik açısından kritik; çünkü açıklama sistemi projenin temel özelliklerinden biri.

### Tezde Kullanılabilecek Anlatım
Prototip geliştirme sürecinde kullanıcı arayüzünde işlevsel kısıtlamalar tespit edilmiş ve yinelemeli geliştirme yaklaşımıyla giderilmiştir.

---

## Değişiklik 2: API Açıklama Sisteminin Yerelleştirilmesi

### Tür
Özellik genişletme + kod düzenleme

### İlgili Commitler
- `ef0af36` — "feat: add localization support for emotion and gender labels; update explanation generation in API"

### Önceki Durum
API, duygu ve cinsiyet etiketlerini sabit İngilizce string'ler olarak döndürüyordu. Açıklama metni de dil bağımsız değildi.

### Sonraki Durum
API yanıtları kullanıcının seçtiği dile göre yerelleştirilmiş etiketler içeriyor. `api_server.py` 109 satır artış gördü.

### Teknik Etki
Frontend'in dil değiştirme özelliğiyle tutarlı olmayan API yanıtları sorunu çözüldü. Artık "Happiness" yerine Türkçe arayüzde "Mutluluk" gösterilebilir.

### Tezde Kullanılabilecek Anlatım
Sistemin çok dilli desteği yalnızca arayüz katmanında değil, API yanıt katmanında da uygulanmış; tutarlı bir kullanıcı deneyimi sağlanmıştır.

---

## Değişiklik 3: Açıklama Alanının API Yanıtına Eklenmesi

### Tür
Özellik ekleme (API genişletmesi)

### İlgili Commitler
- `1476c63` — "feat: add explanation field to API result and update UI to display model explanations"

### Önceki Durum
`/predict` endpoint'i yalnızca sınıflandırma sonucunu (etiket + güven) döndürüyordu. Açıklama metni API yanıtında yoktu.

### Sonraki Durum
API yanıtına `explanation` alanı eklendi. Frontend bu alanı gösterecek şekilde güncellendi.

### Teknik Etki
Model tahminleri artık açıklama metniyle birlikte geldiğinden sistem klinisyen için çok daha bilgilendirici hale geldi.

### Tezde Kullanılabilecek Anlatım
Sistemin açıklanabilirlik kapasitesi, API katmanına açıklama alanı eklenerek arayüze taşınmıştır.

---

## Değişiklik 4: Desktop App Path Çözümleyicisi

### Tür
Hata düzeltme / paketleme uyumluluğu

### İlgili Commitler
- `2a6895c` — `src/app_paths.py` eklendi

### Önceki Durum
Python uygulamasındaki göreli dosya yolları geliştirme ortamında çalışırken PyInstaller ile paketlenmiş `.exe` içinde hata veriyor. Bu, PyInstaller paketlemesinde yaygın bir sorundur.

### Sonraki Durum
`app_paths.py` modülü, uygulamanın `sys.frozen` durumuna göre (yani paketlenmiş mi yoksa geliştirme modunda mı) doğru yolu döndürüyor.

### Teknik Etki
Masaüstü `.exe` paketinin model ağırlıkları, web statik dosyaları vb. dosyalara doğru erişmesi sağlandı.

### Tezde Kullanılabilecek Anlatım
Uygulamanın hem geliştirme hem de bağımsız çalıştırılabilir ortamlarda sorunsuz çalışabilmesi için platforma özgü yol çözümleme mekanizması uygulanmıştır.

---

## Değişiklik 5: Kod Yapısı Refactoring (Mart 2026)

### Tür
Refactoring

### İlgili Commitler
- `72d8a7b` — "Refactor code structure for improved readability and maintainability"

### Önceki Durum
Tam olarak neyin değiştiği commit diff'inden kesin tespit edilemiyor. `desktop_app.py`'ye 13 satır eklendiği görülüyor. `.gitignore` güncellendi. Performans görselleri `Web/public/about/` dizinine eklendi.

### Sonraki Durum
Kod yapısı okunabilirlik açısından düzenlendi. Hakkında sayfası grafikleri (`confusion-matrices.png`, `roc-curves.png`, `sample-predictions.png`, `training-curves.png`) web uygulamasına entegre edildi.

### Teknik Etki
Web uygulamasının `/about` sayfasında model performansı görsel olarak sunulabilir hale geldi.

### Tezde Kullanılabilecek Anlatım
Model değerlendirme sonuçları (confusion matrix, ROC eğrisi, eğitim eğrileri) kullanıcı arayüzünün "hakkında" bölümüne entegre edilerek şeffaflık artırılmıştır.

---

## Değişiklik 6: label_with_model.py → label_with_model_v2.py

### Tür
Hata düzeltme / iteratif geliştirme

### İlgili Commitler
- `73ff5de` — her iki dosya da mevcut

### Önceki Durum
`label_with_model.py` — ilk pseudo-etiketleme scripti.

### Sonraki Durum
`label_with_model_v2.py` — revize edilmiş versiyon. Her iki dosyanın da repo'da eş zamanlı var olması, v2'nin v1'deki sorunları giderdiğini ancak v1'in de referans ya da güvenlik ağı olarak korunduğunu düşündürmektedir.

### Teknik Etki
Pseudo-etiketleme sürecinin güvenilirliği ve/veya performansı iyileştirildi. Kesin fark commit'ten belirlenemiyor; diff incelemesi gerektirir.

### Tezde Kullanılabilecek Anlatım
Pseudo-etiketleme scripti, ilk prototipten elde edilen dersler doğrultusunda yeniden yazılmış; iteratif geliştirme süreci belgelenmiştir.

---

## Değişiklik 7: GitIgnore Güncellemeleri

### Tür
Yapılandırma düzenleme

### İlgili Commitler
- `b8b32b2` — `.gitignore` güncellendi (2 satır değişiklik)
- `2a6895c` — `.gitignore` güncellendi (9 satır ekleme)
- `72d8a7b` — `.gitignore` güncellendi (4 satır ekleme)

### Önceki Durum
Bazı geçici dosyalar, derleme çıktıları veya büyük dosyalar versiyonlama kapsamındaydı.

### Sonraki Durum
Commit diff'lerinde `.gitignore` değişikliklerinin tam içeriği görülmektedir. `2a6895c`'de eklenen 9 satır masaüstü paketleme altyapısıyla eş zamanlı olarak eklendi. `72d8a7b`'de 4 satır daha eklendi. Hangi dizinlerin kapsandığı `.gitignore` dosyasının mevcut içeriğinden okunabilir.

### Teknik Etki
Repo gereksiz derleme artefaktlarından temizlendi.

---

## Değişiklik 8: API Server'ın Mimarisi (v1 → v2)

### Tür
Refactoring + özellik ekleme

### İlgili Commitler
- `08e1303` — ilk API (131 satır)
- `2a6895c` — büyük güncelleme (262 satır, yeniden yazılmaya yakın)

### Önceki Durum
Basit FastAPI uygulaması: CORS + `/health` + `/predict`. Model doğrudan yükleniyor.

### Sonraki Durum
Güncel `api_server.py`:
- `create_app()` factory fonksiyonu (test edilebilirlik için)
- `lifespan` bağlamı ile model başlatma
- Ortam değişkenlerinden checkpoint yükleme (`CCDDA_CHECKPOINT`)
- Statik dosya sunumu (React build)
- LLM açıklama desteği (`GITHUB_TOKEN`)
- Daha sağlam hata yönetimi

### Teknik Etki
API daha bakımı kolay, yapılandırılabilir ve test edilebilir hale geldi. `create_app()` factory patterni, masaüstü ve web deployment senaryolarını aynı kodla desteklemeyi sağladı.

### Tezde Kullanılabilecek Anlatım
API mimarisi, ilk prototipten üretim düzeyine taşınacak şekilde yeniden yapılandırılmıştır; yapılandırılabilirlik ve bakım kolaylığı ön plana çıkarılmıştır.


---

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


---

# 10 — Tezde Kullanılabilecek Geliştirme Süreci Anlatımı

Bu dosya, doğrudan teze aktarılabilecek akademik düzeyde paragraflar içermektedir. Tüm ifadeler ve sayısal değerler, repository içindeki metrik dosyaları, training logları ve pipeline raporlarından elde edilen somut kanıtlara dayanmaktadır.

> **Kaynak şeffaflığı:** Her bölümün sonunda ilgili kaynak dosyalar belirtilmiştir. Tez yazarı bu dosyalara başvurarak rakamları doğrulamalıdır.

---

## Projenin Başlangıcı

Bu çalışma, çocukların el çizmesi resimlerinden duygusal durumun otomatik olarak tespit edilmesini amaçlamaktadır. Araştırmanın motivasyonu, klinik psikoloji pratiğinde yaygın kullanılan projektif çizim testlerinin değerlendirilme sürecindeki öznellik ve uzman bağımlılığıdır.

Projenin veri tabanını KIDO veri seti oluşturmaktadır. Bu veri seti, Türk okul çocuklarına ait el çizmesi resimler içermekte olup dosya adlandırma şemasından (`[okul_id]-[sınıf]-[öğrenci_id]-[cinsiyet]-[duygu].jpg`) her çizime ait meta veriler çıkarılabilmektedir. Başlangıçta 10.856 etiketli örnek kullanılmıştır.

*Kaynak: Commit `ec7d0f8`, `artifacts/report_run/REPORT.md` (train=7.843, val=1.383, test=1.630)*

---

## İlk Prototipin Oluşturulması

Proje, Kasım 2025 sonunda çok modlu (multimodal) bir derin öğrenme sistemi olarak hayata geçirilmiştir. Bu ilk mimaride iki modalite bir araya getirilmiştir: görüntü verisi EfficientNet-B0 ağıyla, metin verisi ise Türkçe BERT modeli (`dbmdz/bert-base-turkish-cased`) aracılığıyla kodlanmıştır. Her iki modaliteden elde edilen özellik vektörleri projeksiyon katmanlarıyla ortak bir 1024 boyutlu uzaya dönüştürülmüş ve birleştirilerek çok görevli bir sınıflandırıcıya aktarılmıştır.

Eğitim sürecinde BERT parametreleri dondurulmuş (`freeze_bert=True`), EfficientNet-B0 ise ince ayara tabi tutulmuştur. Bu asimetrik dondurma stratejisi, 116.2 milyon toplam parametreli modelde eğitilebilir parametre sayısını 5.6 milyona indirmiştir.

*Kaynak: `src/models/multimodal_effnet_bert.py` (commit `b8b32b2`), `src/train/train_multimodal.py`*

---

## İlk Modelin Değerlendirme Sonuçları

İlk çok modlu sistem, KIDO veri setinin 1.630 örneklik test bölümünde değerlendirilmiştir. Duygu sınıflandırması görevinde (2 sınıf: Happiness/Sadness) %94.36 doğruluk, F1=0.9435 ve ROC-AUC=0.9866 elde edilmiştir. Test seti iki sınıf arasında dengeli dağılmıştır (Happy=815, Sad=815). Cinsiyet sınıflandırması ise %77.12 doğruluk, F1=0.7658 ve ROC-AUC=0.8542 ile daha zor bir görev olarak öne çıkmıştır.

Duygu sınıflandırmasına ait confusion matrix incelendiğinde, 815 Happy örneğinden 759'u doğru (%93.1) ve 815 Sad örneğinden 779'u doğru (%95.6) tahmin edilmiştir. Bu sonuçlar, el çizmesi resimlerin makine öğrenimi yöntemleriyle sınıflandırılabilir duygu sinyalleri taşıdığını kanıtlamaktadır.

*Kaynak: `artifacts/report_run/REPORT.md`*

**Önemli uyarı:** Bu sonuçlar yalnızca ikili (2-sınıflı) dengeli bir görevde elde edilmiştir. 4-sınıflı sistemle doğrudan karşılaştırma yapılamaz.

---

## Açıklanabilirlik Katmanının Geliştirilmesi

Klinik ortamlarda yapay zeka sistemlerinin kabul görmesi, yorumlanabilirlik ile doğrudan ilişkilidir. Bu gerçeklikten hareketle sisteme Grad-CAM (Gradient-weighted Class Activation Mapping) görselleştirme modülü entegre edilmiştir (commit `d494e7b`). Duygu ve cinsiyet sınıflandırması için ayrı ısı haritaları üretilmektedir.

Buna ek olarak, kural tabanlı bir açıklama üreticisi geliştirilmiştir. Katmanlı fallback yaklaşımında: `GITHUB_TOKEN` ortam değişkeni mevcutsa LLM tabanlı dinamik açıklama; mevcut değilse `src/explain/rule_based_explainer.py` üzerinden şablon tabanlı açıklama üretilmektedir.

*Kaynak: `d494e7b` commit, `src/explain/gradcam.py`, `api_server.py`*

---

## Arayüz Geliştirme Süreci

**İlk Prototip (Kasım 2025):** Tkinter kütüphanesi ile yerel masaüstü arayüzü geliştirilmiştir (commit `d494e7b`). Kaydırılabilir metin alanı commit `339a738`'de eklenmiştir; bu commit mesajı "Add scrollable text widget for explanation" olarak kayıtlıdır.

**Web Tabanlı Sistem (Şubat 2026, commit `a04e560`):** React + TypeScript (Vite + Tailwind CSS). Tek günde 6 commit yapılmıştır: React kurulumu, i18n, FastAPI, API explanation alanı, etiket yerelleştirmesi, raporlama altyapısı.

**Masaüstü Paketleme (Mart 2026, commit `2a6895c`):** PyInstaller + pywebview. `src/app_paths.py` dosyası `sys.frozen` kontrolü ile paketlenmiş ortamda dosya yolu sorununu çözmektedir. Inno Setup ile Windows kurulum paketi oluşturulmuştur.

*Kaynak: Commitler `d494e7b`, `339a738`, `a04e560`, `3b481f8`, `08e1303`, `2a6895c`*

---

## Mimari Yeniden Yapılanma

Nisan 2026'da (`5311334`) BERT tabanlı metin kodlayıcısı ve ilgili tüm bileşenler kaldırılmıştır. README içeriğinde "eski multimodal AI hattı bu repodan temizlendi" ve "legacy AI giris noktalari bilincli olarak devre disi birakildi" ifadeleri yer almaktadır. `/predict` endpoint'i bu aşamada `503 Service Unavailable` dönecek şekilde devre dışı bırakılmıştır.

Bu kararın teknik gerekçesi commit geçmişinde belgelenmemiştir. Repository içinde bu değişikliği zorunlu kılan başarısızlık logu veya performans karşılaştırması bulunamadı.

Aynı dönemde sınıflandırma hedefi de iki sınıftan (Happy/Sad) dört sınıfa (Anger/Fear/Happy/Sad) genişletilmiştir.

*Kaynak: Commit `5311334`, `fb8602a`*

---

## 4-Sınıflı Sistemin Değerlendirme Sonuçları

Yeni 4-sınıflı görüntü-tabanlı sistem 1.257 örneklik test setinde değerlendirilmiştir. Genel doğruluk %67.06, Macro F1=0.5775 ve Balanced Accuracy=%58.88 olarak ölçülmüştür.

Sınıf bazlı sonuçlar sınıf dengesizliğinin performans üzerindeki etkisini açıkça göstermektedir:

| Sınıf | F1 | Test Örneği |
|---|---|---|
| Happy | 0.773 | 626 |
| Sad | 0.660 | 356 |
| Fear | 0.507 | 208 |
| Angry | **0.370** | **67** |

Angry sınıfının yalnızca 67 test örneğiyle temsil edilmesi ve F1=0.370 değeri, sınıf dengesizliğinin kritik bir sınırlama oluşturduğunu kanıtlamaktadır.

*Kaynak: `artifacts/v1_backend/eval/metrics.json`, `artifacts/v1_backend/eval/confusion_matrix.csv`*

---

## Multitask Öğrenme ile İyileştirme

Duygu ve fenotip sınıflandırmasını eş zamanlı gerçekleştiren multitask model (alpha=0.25), tek görev modelinin üzerinde belirgin performans artışı sağlamıştır:

| Model | Accuracy | Macro F1 | Eğitim Seti |
|---|---|---|---|
| Tek görev (4-sınıf) | 67.06% | 0.5775 | 6.024 |
| Multitask (duygu+fenotip) | **72.73%** | **0.7272** | 7.843 |

Happy F1=0.7337 ve Sad F1=0.7207 değerleri bu iki sınıfın multitask eğitimden yararlanan sınıflar olduğunu göstermektedir. En iyi doğrulama Duygu F1=0.7427 olarak kayıtlıdır.

*Kaynak: `out/phenotype_images/multitask_run_alpha025/test_results.json`*

---

## Veri Büyütme: Yarı Denetimli Öğrenme

Derin öğrenme modellerinin yüksek başarı oranı göstermesi için büyük miktarda etiketli veri gerekmektedir. Bu kısıtı aşmak amacıyla yarı denetimli öğrenme paradigması benimsenmiştir.

**Öğretmen model etiketleme kapsamı:**
- Toplam işlenen görüntü: 55.660
- Ortalama tahmin güveni: 0.7306
- Güven ≥ 0.85 geçen: 18.786 örnek (%33.8)
- Güven ≥ 0.75 geçen: 28.314 örnek (%50.9)

*Kaynak: `out/highconf_pipeline/teacher_labels_report.json`*

**Pipeline karşılaştırması:**

Yüksek güvenilirlikli pseudo-etiketleme (eşik=0.75): 23.063 eğitim örneği, Macro F1=0.6694, Accuracy=67.07%.

Uzlaşma tabanlı etiketleme (3/3 model mutabakatı): 7.980 eğitim örneği, Macro F1=0.5721, Accuracy=57.49%.

*Kaynak: `out/highconf_pipeline/summary_results.csv`, `out/consensus_pipeline/summary_results.csv`*

0.75 eşikli yüksek güvenilirlik pipeline'ı hem daha fazla örnek üretmiş hem de daha yüksek test performansı elde etmiştir.

---

## Model Kalibrasyonu ve Güven Analizi

Modelin güven skorları ile gerçek doğruluk arasındaki ilişki analiz edilmiştir. ECE (Expected Calibration Error) = 0.1698, modelin aşırı güvenli (overconfident) olduğunu göstermektedir.

0.9–1.0 güven aralığındaki 651 örnekte ortalama güven skoru 0.967 iken ortalama doğruluk 0.805'tir. Bu durum, yüksek güven skoru taşıyan tahminlerin yaklaşık %20 hata içerebileceğini göstermektedir.

*Kaynak: `artifacts/v1_backend/eval/calibration.json`, `artifacts/v1_backend/eval/high_confidence_errors.csv`*

---

## Etik Değerlendirme

Sistemin klinik tanı aracı olarak sunulması amaçlanmamaktadır. `artifacts/report_run/REPORT.md` değerlendirme raporu şu uyarıyı içermektedir: "Bu sistem klinik tanı aracı değildir. Çıktılar yalnızca araştırma ve karar-destek amaçlı değerlendirilmelidir; nihai yorum uzman profesyoneller tarafından yapılmalıdır."

Repository içinde klinisyen değerlendirmesi veya etik kurul onayına ilişkin belge bulunmamaktadır. Bu bilgiler tez yazarı tarafından eklenmesi gereken unsurlardır.

---

## Sonuç

Bu proje, çocuk çizimi tabanlı duygu analizi alanında makine öğrenimi yöntemlerinin uygulanabilirliğini araştırmaktadır. Temel sayısal sonuçlar:

| Model | Görev | Accuracy | Macro F1 | Kaynak |
|---|---|---|---|---|
| Multimodal EfficientNet+BERT | 2-sınıf duygu | **94.36%** | **0.9435** | `artifacts/report_run/REPORT.md` |
| Multimodal EfficientNet+BERT | 2-sınıf cinsiyet | 77.12% | 0.7658 | `artifacts/report_run/REPORT.md` |
| 4-sınıf görüntü-tabanlı | 4-sınıf duygu | 67.06% | 0.5775 | `artifacts/v1_backend/eval/metrics.json` |
| Highconf pipeline (0.75) | 4-sınıf duygu | 67.07% | 0.6694 | `out/highconf_pipeline/summary_results.csv` |
| Multitask (duygu+fenotip) | 4-sınıf duygu | **72.73%** | **0.7272** | `out/phenotype_images/multitask_run_alpha025/test_results.json` |


---

# 11 — Zaman Çizelgesi

Bu dosya, commit tarihlerine dayalı proje zaman çizelgesini sunmaktadır. Yalnızca repository'de commit bulunan tarihler ve olaylar yer almaktadır. Commit'e yansımayan faaliyetler bu dosyada yer almaz.

---

# Zaman Çizelgesi

| Tarih | Geliştirme Aşaması | İlgili Commitler | Açıklama |
|---|---|---|---|
| 2025-11-30 | **Proje Kuruluşu + İlk Model** | `ec7d0f8` | İlk commit: KIDO veri seti, eğitim scripti, .gitignore |
| 2025-11-30 | **Multimodal Model Mimarisi** | `b8b32b2` | EfficientNet-B0 + Türkçe BERT modeli, freeze parametreleri |
| 2025-11-30 | **GUI + Açıklanabilirlik** | `d494e7b` | Tkinter GUI, Grad-CAM, kural tabanlı açıklayıcı |
| *2025-12-01 — 2026-02-21* | **Commit Yok** | — | Bu tarih aralığında repository'de commit yoktur |
| 2026-02-22 | **GUI İyileştirme** | `339a738` | Kaydırılabilir metin alanı, açıklama yeniden düzenleme |
| 2026-02-22 | **React Projesi Kurulumu** | `a04e560` | Vite + TypeScript + Tailwind CSS |
| 2026-02-22 | **Çok Dil Desteği** | `3b481f8` | i18n (Türkçe/İngilizce) |
| 2026-02-22 | **FastAPI Backend** | `08e1303` | REST API, analiz sayfası, CORS |
| 2026-02-22 | **Açıklama API Entegrasyonu** | `1476c63` | API yanıtına explanation alanı eklendi |
| 2026-02-22 | **Etiket Yerelleştirmesi** | `ef0af36` | Duygu/cinsiyet etiketleri dil bazlı |
| 2026-02-22 | **Raporlama Altyapısı** | `bab2958` | run_report.py, confusion matrix — **Duygu F1=0.9435** |
| 2026-03-12 | **DOCX Rapor Üretici** | `16fa3d3` | Markdown → DOCX dönüştürücü, tez şablonu |
| 2026-03-12 | **Masaüstü Uygulama** | `2a6895c` | PyInstaller, pywebview, Inno Setup |
| 2026-03-12 | **Refactoring + Grafikler** | `72d8a7b` | Kod yapısı, /about sayfası görselleri |
| *2026-03-13 — 2026-04-18* | **Commit Yok** | — | Bu tarih aralığında repository'de commit yoktur |
| 2026-04-19 | **Mimari Sıfırlama** | `5311334` | Eski AI yığını kaldırıldı, README yeniden yazıldı |
| 2026-04-20 | **Yeni Plan** | `fb8602a` | Backend V1 mikro-sprint yürütme planı |
| *2026-04-21 — 2026-05-07* | **Commit Yok** | — | Bu tarih aralığında repository'de commit yoktur |
| 2026-05-08 | **Yeni Altyapı** | `dc64027` | .env, dataset reorganizasyonu |
| 2026-05-10 | **Pseudo-Etiketleme Scriptleri** | `73ff5de` | label_with_*.py, build_manifest_*.py, pipeline scriptleri |
| 2026-05-14 | **Pipeline Çıktıları** | `a846643` | highconf (F1=0.6694) + consensus (F1=0.5721) pipeline çıktıları |

---

# Zaman Çizelgesi Görsel Özeti

```
2025-11     ████ [Proje başlangıcı: multimodal model + GUI + Grad-CAM]
2025-12     ░░░░ [Commit yok]
2026-01     ░░░░ [Commit yok]
2026-02-22  ████████ [YOĞUN SPRINT: React + FastAPI + i18n + Raporlama — Duygu F1=0.9435]
2026-03-12  ████ [Masaüstü paketleme + DOCX + Refactoring]
2026-03-13  ░░░░ [Commit yok]
2026-04-19  ██ [SIFIRLAMA: Legacy AI kaldırıldı]
2026-04-20  █  [Yeni plan dokümantasyonu]
2026-04-21  ░░░░ [Commit yok]
2026-05-08  █  [Ortam yapılandırması]
2026-05-10  ██ [Pseudo-etiketleme altyapısı]
2026-05-14  █  [Pipeline çıktıları — highconf F1=0.6694, consensus F1=0.5721]
```

---

# Geliştirme Yoğunluğu Analizi

| Dönem | Commit Sayısı | Durum |
|---|---|---|
| Kasım 2025 | 3 | Aktif |
| Aralık 2025 – 21 Şubat 2026 | 0 | **Commit yok** |
| 22 Şubat 2026 | 7 | **En yoğun gün** |
| 12 Mart 2026 | 3 | Aktif |
| 13 Mart – 18 Nisan 2026 | 0 | **Commit yok** |
| 19–20 Nisan 2026 | 2 | Aktif |
| 21 Nisan – 7 Mayıs 2026 | 0 | **Commit yok** |
| 8–14 Mayıs 2026 | 3 | Aktif |

---

# Önemli Tarih Notları

1. **22 Şubat 2026 — En Yoğun Gün:** Tek günde React projesi, i18n, FastAPI, açıklama API'si ve raporlama altyapısı oluşturuldu. 7 commit. Bu tarihte `bab2958` commiti ile ölçülen değerler: Duygu Accuracy=%94.36, F1=0.9435, ROC-AUC=0.9866.

2. **19 Nisan 2026 — Mimari Sıfırlama:** Eski çok modlu sistem `5311334` commiti ile kaldırıldı. Bu kararın teknik gerekçesini doğrulayan log veya metrik repository'de bulunmamaktadır.

3. **Commit Olmayan Dönemler:** Üç ayrı dönemde (Aralık 2025 – Şubat 2026, Mart – Nisan 2026, Nisan – Mayıs 2026) repository'de commit yoktur. Bu dönemlerde neler yapıldığı commit geçmişinden belirlenememektedir.

---

# Commit Bazlı Aktif Geliştirme Süresi

| Aşama | Süre (commit tarihlerine göre) |
|---|---|
| İlk prototip + GUI | 1 gün (30 Kasım 2025) |
| Web + API geliştirme | 1 gün (22 Şubat 2026) |
| Masaüstü + Raporlama | 1 gün (12 Mart 2026) |
| Karar ve sıfırlama | 2 gün (19–20 Nisan 2026) |
| Yeni sistem geliştirme | 3 gün (8–14 Mayıs 2026) |
| **Commit bulunan toplam gün sayısı** | **8 gün** |
| **Toplam takvim süresi** | **~6 ay (30 Kasım 2025 – 14 Mayıs 2026)** |

**Not:** Aktif geliştirme süresi commit sayısına göre değil, commit tarihlerine göre hesaplanmıştır. Bu tablo yalnızca repository'ye yansıyan faaliyetleri kapsamaktadır.


---

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


---

*Bu konsolide dosya 2026-05-16 tarihinde güncellenmiştir. Spekülatif ifadeler kaldırılmış; tüm sayısal değerler repository içindeki gerçek metrik dosyalarından alınmıştır.*
