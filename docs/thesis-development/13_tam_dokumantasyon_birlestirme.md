# 13 — TAM DÖKÜMANTASYON BİRLEŞTİRME
# CCDDA Projesi — Tez Geliştirme Süreci Tam Arşivi

> Bu dosya, `docs/thesis-development/` klasöründeki tüm dokümantasyon dosyalarının (00–12 ve README) içeriğini tek bir belgede birleştirir. Diğer dosyalar silinmemiştir; bu dosya yalnızca kolaylık amaçlıdır.
>
> Oluşturulma: Mayıs 2026 | Kaynak: Git commit geçmişi analizi

---

# İÇİNDEKİLER

1. [Proje Genel Özet](#00--proje-genel-özet)
2. [Commit Kronolojisi](#01--commit-kronolojisi)
3. [Geliştirme Aşamaları](#02--geliştirme-aşamaları)
4. [Deneyler ve Denemeler](#03--deneyler-ve-denemeler)
5. [Karşılaşılan Problemler ve Çözümler](#04--karşılaşılan-problemler-ve-çözümler)
6. [Teknik Kararlar](#05--teknik-kararlar)
7. [Sistem Mimarisi Evrimi](#06--sistem-mimarisi-evrimi)
8. [Özellik Bazlı Gelişim](#07--özellik-bazlı-gelişim)
9. [Hata Düzeltmeleri ve Refactoring](#08--hata-düzeltmeleri-ve-refactoring)
10. [Test, Doğrulama ve Sınırlamalar](#09--test-doğrulama-ve-sınırlamalar)
11. [Tezde Kullanılabilecek Anlatım](#10--tezde-kullanılabilecek-anlatım)
12. [Zaman Çizelgesi](#11--zaman-çizelgesi)
13. [Eksik Bilgiler ve Dürüst Notlar](#12--eksik-bilgiler-ve-dürüst-notlar)
14. [Klasör README'si](#readme--klasör-rehberi)

---

---

# 00 — Proje Genel Özet

## Projenin Adı

**CCDDA** — *Children's Drawing-Based Duygu/Emotion Analizi*

Proje dizin adı `CCDDA`'dır. Commit geçmişi ve dosya yapısından çıkarıldığı kadarıyla bu kısaltma, "Children's Chart/Drawing Duygu Analizi" ya da benzer bir Türkçe-İngilizce karışık isimlendirmeye karşılık gelmektedir. Kesin açılımı commit ya da README'de belirtilmemiştir.

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

- **KIDO Veri Kümesi**: Türk okul çocuklarına ait el çizmesi resimler; `[okul_id]-[sınıf]-[öğrenci_id]-[cinsiyet]-[duygu].jpg` formatı
- **HuggingFace Parquet Dosyaları**: `Dataset/huggingface/`
- **Roboflow — Drawing Facial Emotions**: `Dataset/Images/Emotion_Roboflow_DrawingFacialEmotions/`
- **SigLIP 4-class**: `Dataset/Images/Emotion_SigLIP_4Class/`
- **Türetilmiş Veri Kümeleri**: `out/highconf_pipeline/`, `out/consensus_pipeline/`

---

## Tez Bağlamında Araştırma Soruları

1. Çocuk çizimleri yalnızca görsel özelliklerinden hareketle duygu sınıflandırmasına uygun mudur?
2. Çok modlu yaklaşımlar görüntü-only yaklaşımdan daha iyi performans gösterir mi?
3. Pseudo-etiketleme ile veri artırımı sınıflandırma başarısını iyileştirebilir mi?
4. Bu sistem klinisyenlere pratik destek sağlayabilecek kullanılabilirlik düzeyine ulaşabilir mi?

---

## Mevcut Durum (Mayıs 2026)

- Eski AI katmanı Nisan 2026'da kaldırıldı.
- `/predict` endpoint'i `503 reset_in_progress` döndürüyor.
- `run_highconf_pipeline.py` ve `run_consensus_pipeline.py` aktif geliştirme aşamasında.
- Frontend ve masaüstü kabuğu korunmuş; yeni modeli bekliyor.

---

---

# 01 — Commit Kronolojisi

Bu dosya, projenin tüm commit geçmişini en eski committen en yeniye doğru, teknik analiz ve tez bağlamında yorumlarıyla listeler.

## Commit Tablosu

| # | Commit ID | Tarih | Commit Mesajı | Kategori | Değişen Dosyalar (Özet) | Teknik Yorum |
|---|---|---|---|---|---|---|
| 1 | `ec7d0f8` | 2025-11-30 | first commit | `setup` | `.gitignore`, `Dataset/Images/Education/test/Primary/` (çok sayıda resim), `src/train/train_multimodal.py` | Projenin başlangıç anı. Hem veri seti hem de eğitim kodu aynı committe. KIDO görüntüleri ve çok modlu EfficientNet+BERT eğitim scripti birlikte eklendi. |
| 2 | `b8b32b2` | 2025-11-30 | Ağırlık düzenleme | `feature` | `src/models/multimodal_effnet_bert.py`, `src/train/train_multimodal.py` | Model mimarisi tanımlandı. EfficientNet-B0 + Türkçe BERT birleştirildi; duygu ve cinsiyet kafaları oluşturuldu. "Ağırlık düzenleme" muhtemelen freeze/unfreeze parametrelerine atıfta bulunuyor. |
| 3 | `d494e7b` | 2025-11-30 | Ezber cümleler ve GUI eklendi | `feature` + `ui` | `src/app/gui_multimodal.py`, `src/app/tk_app.py`, `src/explain/gradcam.py`, `src/explain/rule_based_explainer.py` ve diğerleri | Büyük commit. Tkinter GUI, Grad-CAM, kural tabanlı açıklayıcı eklendi. |
| 4 | `339a738` | 2026-02-22 | Add scrollable text widget for explanation... | `ui` + `refactor` | `src/app/gui_multimodal.py`, `src/app/tk_app.py` | ~3 aylık boşluktan sonra ilk commit. Kaydırılabilir metin alanı eklendi. |
| 5 | `a04e560` | 2026-02-22 | feat: initialize React project with Vite... | `setup` | `Web/` dizininin tamamı | Tkinter'dan web tabanlı arayüze geçiş. React + Vite + TypeScript + Tailwind CSS kuruldu. |
| 6 | `3b481f8` | 2026-02-22 | feat: implement internationalization... | `feature` | `Web/src/` (i18n) | Türkçe/İngilizce çoklu dil desteği (i18next) eklendi. |
| 7 | `08e1303` | 2026-02-22 | feat: enhance analysis page... add FastAPI backend | `feature` + `api` | `Web/src/App.tsx`, `api_server.py` (yeni, 131 satır), `requirements.txt` | İlk FastAPI arka ucu. `/health` ve `/predict` endpoint'leri. CORS middleware. |
| 8 | `1476c63` | 2026-02-22 | feat: add explanation field to API result... | `feature` | `Web/src/App.tsx`, `api_server.py` | API yanıtına açıklama alanı eklendi; UI güncellendi. |
| 9 | `ef0af36` | 2026-02-22 | feat: add localization support for emotion... | `feature` | `Web/src/App.tsx`, `api_server.py` (+109 satır) | Duygu/cinsiyet etiketleri için yerelleştirme desteği. |
| 10 | `bab2958` | 2026-02-22 | Add report runner script and configuration | `test` + `docs` | `artifacts/report_run/REPORT.md`, confusion matrix, ROC curve görselleri | Model değerlendirme ve raporlama altyapısı. |
| 11 | `16fa3d3` | 2026-03-12 | Add script to generate DOCX reports | `feature` | `build_report_docx.py`, `Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx` | Markdown → DOCX dönüştürücü. Tez şablonu eklendi. |
| 12 | `2a6895c` | 2026-03-12 | feat: add desktop application with embedded FastAPI | `feature` | `desktop_app.py`, `desktop_app.spec`, `src/app_paths.py`, `Web/src/App.tsx` (+346 satır) | Masaüstü uygulama altyapısı: PyInstaller, pywebview, Inno Setup. |
| 13 | `72d8a7b` | 2026-03-12 | Refactor code structure... | `refactor` | `desktop_app.py` (+13 satır), `Web/public/about/` görselleri | Kod yapısı ve okunabilirlik düzenlemesi. Performans grafikleri eklendi. |
| 14 | `5311334` | 2026-04-19 | chore: remove legacy dataset and reset old AI stack | `cleanup` | `Dataset/Images/Education/` (silindi), eski AI modülleri | **Kritik mimari sıfırlama.** Eski çok modlu AI kaldırıldı. |
| 15 | `fb8602a` | 2026-04-20 | feat: add comprehensive execution plan... | `docs` | Plan dosyaları | Backend V1 mikro-sprint yürütme planı. |
| 16 | `dc64027` | 2026-05-08 | Auto-commit: save changes before push | `setup` | `.env`, `.env.example`, Claude config | Ortam değişkeni altyapısı. Araç tarafından otomatik oluşturulmuş. |
| 17 | `73ff5de` | 2026-05-10 | Save: push all local changes | `feature` + `cleanup` | `Dataset/Images/Emotion_4Class/`, pseudo-etiketleme scriptleri | Yeni 4-sınıflı veri yapısı, pseudo-etiketleme scriptleri eklendi/güncellendi. |
| 18 | `a846643` | 2026-05-14 | chore: add new phenotype pipelines and output files | `feature` | `out/consensus_pipeline/`, `out/highconf_pipeline/` (büyük CSV'ler) | Pipeline çıktıları: consensus ve highconf manifest'leri üretildi. |

## Commit Kategori Dağılımı

| Kategori | Commit Sayısı | Commitler |
|---|---|---|
| `setup` | 2 | ec7d0f8, a04e560 |
| `feature` | 9 | b8b32b2, d494e7b, 08e1303, 1476c63, ef0af36, 2a6895c, dc64027, 73ff5de, a846643 |
| `ui` | 2 | 339a738, a04e560 |
| `refactor` | 2 | 339a738, 72d8a7b |
| `api` | 1 | 08e1303 |
| `test` + `docs` | 2 | bab2958, fb8602a |
| `cleanup` | 2 | 5311334, 73ff5de |

## Önemli Gözlemler

1. İlk commit büyük — yerel geliştirme tamamlandıktan sonra GitHub'a yüklendi.
2. 3 aylık boşluk (Commit 3–4 arası) — commitlenmemiş çalışmalar olabilir.
3. 22 Şubat 2026'da tek günde 7 commit — büyük bir web geliştirme sprinti.
4. Commit 14 (5311334) projenin en kritik dönüm noktasıdır.
5. Son commitlerde anlamsız mesajlar ("Save", "Auto-commit") — diff içeriğinden analiz edildi.

---

---

# 02 — Geliştirme Aşamaları

## Aşama 1: Proje Kurulumu ve İlk Çok Modlu Model

**Dönem:** 30 Kasım 2025 | **Commitler:** `ec7d0f8`, `b8b32b2`, `d494e7b`

### Yapılan İşler
- KIDO veri seti projeye dahil edildi (`Dataset/Images/Education/test/Primary/`)
- Çok modlu sinir ağı mimarisi tasarlandı:
  - **Görüntü:** EfficientNet-B0 (ImageNet ağırlıkları)
  - **Metin:** `dbmdz/bert-base-turkish-cased`
  - **Birleştirme:** Projeksiyon → 512 boyut → Concat [1024]
  - **Çıkış:** Duygu kafası (2 sınıf) + Cinsiyet kafası (2 sınıf)
- EfficientNet eğitilebilir, BERT dondurulmuş başlatıldı
- Tkinter GUI, Grad-CAM, kural tabanlı açıklayıcı eklendi

### Teknik Değerlendirme
Projenin başından itibaren çok görevli öğrenme hedeflendi. BERT'in dondurulmuş başlatılması küçük veri setlerinde aşırı öğrenmeyi azaltmak için standart bir stratejidir. "Ezber cümleler" ifadesi, kural tabanlı açıklayıcıdaki şablon cümlelere işaret etmektedir.

### Tezde Kullanılabilecek Anlatım
Projenin ilk aşamasında çok görevli bir derin öğrenme mimarisi benimsenmiştir. Görüntü bilgisi EfficientNet-B0 ile, metin bilgisi Türkçe BERT modeliyle kodlanmış; özellikler birleştirilerek iki bağımsız sınıflandırma kafasına aktarılmıştır.

---

## Aşama 2: Tkinter GUI Olgunlaştırma

**Dönem:** Kasım 2025 – Şubat 2026 | **Commit:** `339a738`

### Yapılan İşler
- Kaydırılabilir metin alanı eklendi
- Açıklama üretim mantığı yeniden düzenlendi

### Teknik Değerlendirme
~3 aylık boşluktan sonra ilk commit. Küçük ama işlevsel UI iyileştirmesi.

---

## Aşama 3: Web Arayüzü ve FastAPI Backend'e Geçiş

**Dönem:** 22 Şubat 2026 | **Commitler:** `a04e560`, `3b481f8`, `08e1303`, `1476c63`, `ef0af36`, `bab2958`

### Yapılan İşler
- Tkinter'dan React web uygulamasına geçiş
- React + Vite + TypeScript + Tailwind CSS kuruldu
- i18next ile Türkçe/İngilizce dil desteği
- FastAPI arka ucu (`api_server.py`) oluşturuldu
- API yanıtına açıklama alanı ve yerelleştirilmiş etiketler eklendi
- Confusion matrix ve ROC eğrisi üretildi

### Teknik Değerlendirme
Tek günde 7 commit — yoğun bir sprint. Vite proxy yapılandırması React→FastAPI iletişimini sağladı.

### Tezde Kullanılabilecek Anlatım
Yerel masaüstü arayüzünden modern web teknolojilerine geçilmiş; React ve FastAPI kullanılarak istemci-sunucu mimarisi oluşturulmuş; çok dilli arayüz desteği sağlanmıştır.

---

## Aşama 4: Masaüstü Paketleme ve Raporlama

**Dönem:** 12 Mart 2026 | **Commitler:** `16fa3d3`, `2a6895c`, `72d8a7b`

### Yapılan İşler
- Markdown → DOCX dönüştürücü geliştirildi
- Tez belgesi şablonu eklendi
- PyInstaller + pywebview masaüstü uygulaması oluşturuldu
- Inno Setup Windows kurulum paketi scripti yazıldı
- Web uygulamasına performans grafikleri eklendi

### Tezde Kullanılabilecek Anlatım
PyInstaller ile Windows çalıştırılabilir paketi oluşturulmuş; internet bağlantısı gerektirmeyen klinik ortamlarda kullanım mümkün hale getirilmiştir.

---

## Aşama 5: Kritik Mimari Sıfırlama

**Dönem:** 19–20 Nisan 2026 | **Commitler:** `5311334`, `fb8602a`

### Yapılan İşler
- Eski AI yığını tamamen kaldırıldı (BERT, multimodal füzyon, eski checkpoint'ler)
- README yeniden yazıldı
- Backend V1 için mikro-sprint planı oluşturuldu

### Teknik Değerlendirme
Projenin en önemli dönüm noktası. Geçişin kesin nedeni commit'te belirtilmemiş. Olası gerekçeler: performans yetersizliği, metin verisi kalitesi, akademik odak değişimi, 4-sınıflı hedefe geçiş ihtiyacı.

### Tezde Kullanılabilecek Anlatım
Çok modlu yaklaşımdan vazgeçilerek yalnızca görüntü tabanlı mimariye geçilmiş; sınıf sayısı da dörde (Anger, Fear, Happiness, Sadness) genişletilmiştir.

---

## Aşama 6: Yeni Veri Hattı — Pseudo-Etiketleme

**Dönem:** 8–14 Mayıs 2026 | **Commitler:** `dc64027`, `73ff5de`, `a846643`

### Yapılan İşler
- Yeni 4-sınıflı veri kümesi (`Dataset/Images/Emotion_4Class/`) oluşturuldu
- Pseudo-etiketleme scriptleri geliştirildi (`label_with_hf.py`, `label_with_ollama.py`, `label_with_model.py`, `label_with_model_v2.py`)
- Veri manifesti scriptleri yazıldı (5 farklı)
- High-confidence ve consensus pipeline'ları çalıştırıldı
- Çıktı manifests'leri üretildi (~23K ve ~8.3K örnek)

### Teknik Değerlendirme
Öğretmen-öğrenci öğrenme yaklaşımı. Consensus pipeline gürültüyü azaltmak için güçlü bir yöntem.

### Tezde Kullanılabilecek Anlatım
Veri kıtlığını aşmak amacıyla pseudo-etiketleme benimsenmiş; güven eşiği ve çoklu model mutabakatı kriterleriyle etiket kalitesi artırılmıştır.

---

---

# 03 — Deneyler ve Denemeler

## Deneme 1: Çok Modlu Mimari (Görüntü + Metin)

**Kanıt:** `ec7d0f8`, `b8b32b2` — `src/models/multimodal_effnet_bert.py`

**Ne Denenmiş Olabilir?** Çizimi yapan çocuğun meta verisi veya metin açıklamaları görüntüyle birleştirildi. "Metin" verisinin tam içeriği commit'lerden net belirlenemiyor (`REPORT.md`'de `text_tr`, `text_en` sütunlarına atıf var).

**Sonuç:** Nisan 2026'da tamamen kaldırıldı (`5311334`).

**Neden Değiştirilmiş Olabilir?** Metin kalitesi yetersiz olabilir, araştırma odağı daraltılmış olabilir veya 4-sınıflı hedefe geçiş bu değişimi zorunlu kılmış olabilir.

**Tezde Nasıl Anlatılabilir?** İlk sistemde çok modlu yaklaşım denenmiş; ancak görüntü-metin füzyonunun araştırma sorusuna katkısı sınırlı kalmış, sistem yalnızca görüntü modalitesine odaklanacak şekilde yeniden tasarlanmıştır.

---

## Deneme 2: İkili Sınıflandırmadan 4-Sınıflı Sınıflandırmaya

**Kanıt:** `ec7d0f8` (2 sınıf: Happiness/Sadness), `73ff5de` (4 sınıf: Anger/Fear/Happy/Sad)

**Ne Denenmiş Olabilir?** Başlangıçta ikili sınıflandırma hedeflendi. Klinik psikoloji taksonomileriyle uyum için 4 sınıfa genişletme kararı alındı.

**Tezde Nasıl Anlatılabilir?** İkili sınıflandırmadan 4-sınıflı taksonomiye (Öfke, Korku, Mutluluk, Üzüntü) geçiş, klinik psikoloji literatürüyle uyumu artırmak amacıyla gerçekleştirilmiştir.

---

## Deneme 3: Tkinter GUI → React Web Arayüzü

**Kanıt:** `d494e7b` (Tkinter), `a04e560` (React)

**Ne Denenmiş Olabilir?** İlk prototip için Tkinter hızlı tercih; ancak dağıtım ve erişilebilirlik sınırlamaları React'e geçişi tetikledi.

**Sonuç:** Tkinter kodu hâlâ `src/app/`'da mevcut, aktif geliştirme React'te sürüyor.

---

## Deneme 4: Farklı Pseudo-Etiketleme Stratejileri

**Kanıt:** `label_with_hf.py`, `label_with_ollama.py`, `label_with_model.py`, `label_with_model_v2.py`

En az üç strateji denenmiş:
1. Kendi eğitimli model
2. Büyük dil modeli (Qwen2.5-VL)
3. Çoklu model uzlaşması

Güven eşiği olarak 0.75 ve 0.85 denenmiş.

---

## Deneme 5: Farklı EfficientNet Varyantları

**Kanıt:** İlk modelde B0; `run_highconf_pipeline.py`'de B2 ve B3 import'ları var.

EfficientNet B0 → B2/B3 yükseltmesi denenmiş. Kesin tercih commit'lerden belirlenemiyor.

---

## Deneme 6: Çoklu Veri Manifesti Yaklaşımları

**Kanıt:** 5 farklı manifest scripti: `build_manifest_kido.py`, `build_manifest_expanded.py`, `build_manifest_v2.py`, `build_manifest_final.py`, `build_manifest_qwen.py`

Hangi veri kaynaklarının nasıl birleştirileceği üzerine birden fazla strateji denenmiş.

---

---

# 04 — Karşılaşılan Problemler ve Çözümler

## Problem 1: Metin Açıklamaları Statik Kalmaktaydı

**Kanıt:** `d494e7b` "ezber cümleler" ifadesi → `src/explain/rule_based_explainer.py`

**Çözüm:** Kural tabanlı açıklayıcı korunurken API'ye dinamik LLM açıklama desteği eklendi. Katmanlı fallback: LLM varsa dinamik, yoksa kural tabanlı.

**Tezde:** Açıklanabilirlik katmanı kural tabanlı fallback mekanizmasıyla desteklenmiş; Grad-CAM ile birlikte çok katmanlı XAI çerçevesi sunulmuştur.

---

## Problem 2: Tkinter'da Uzun Açıklamalar Görüntülenemiyordu

**Kanıt:** `339a738` "Add scrollable text widget"

**Çözüm:** `Text` widget + `Scrollbar` kombinasyonu.

---

## Problem 3: Frontend-Backend İletişimi (CORS)

**Kanıt:** `08e1303`'te `vite.config.ts` güncellendi.

**Çözüm:** Vite proxy yapılandırması + FastAPI CORS middleware.

---

## Problem 4: Eski AI Yığınının Sürdürülemezliği

**Kanıt:** `5311334` — "remove legacy dataset and reset old AI stack"

**Çözüm:** Radikal temizlik. BERT, eski veri, eski modüller kaldırıldı. API geçici 503 döndürecek şekilde devre dışı bırakıldı.

---

## Problem 5: Etiketlenmiş Veri Kıtlığı

**Çözüm:** Üç katmanlı yaklaşım:
1. Harici veri (HuggingFace parquet, Roboflow)
2. High-confidence pseudo-etiketleme (≥0.75 / ≥0.85)
3. Consensus etiketleme (3/3 mutabakat)

**Sonuç:** `manifest_highconf_075.csv` ~23.000, `manifest_highconf_085.csv` ~19.000 örnek.

---

## Problem 6: Masaüstü Dağıtımı — Paketleme Yolu Sorunu

**Kanıt:** `2a6895c`'de `src/app_paths.py` eklendi.

**Çözüm:** `sys.frozen` durumuna göre dinamik yol çözümleme.

---

## Problem 7: Model Değerlendirme Standardizasyonu

**Kanıt:** `bab2958` — `run_report.py` ve `run_args.json` eklendi.

**Sonuçlar (İlk Model):**
| Görev | Accuracy | F1 (macro) | ROC-AUC |
|---|---|---|---|
| Duygu (2 sınıf) | %94.36 | 0.9435 | 0.9866 |
| Cinsiyet (2 sınıf) | %77.12 | 0.7658 | 0.8542 |

---

---

# 05 — Teknik Kararlar

## Karar 1: EfficientNet-B0 Görüntü Kodlayıcı

**Karar:** İlk model için EfficientNet-B0 seçildi.

**Kanıt:** `src/models/multimodal_effnet_bert.py` (`b8b32b2`)

**Gerekçe:** Parametre-verimlilik dengesi üstün; ImageNet ön eğitimi küçük veri setlerinde kritik avantaj. Daha sonra B2/B3'e yükseltme kolaylığı (aynı aile).

**Dezavantaj:** Çizim görüntüleri fotoğraflardan farklı dağılım gösterir; ImageNet ağırlıkları tam uygun olmayabilir.

---

## Karar 2: Türkçe BERT (dbmdz/bert-base-turkish-cased)

**Karar:** Metin kodlayıcı olarak Türkçe BERT.

**Kanıt:** `src/train/train_multimodal.py` default argümanı.

**Gerekçe:** Türk okul çocukları veri seti; Türkçe morfolojisini iyi temsil eder. Nisan 2026'da kaldırıldığı için pratik etkisi sınırlı kalmıştır.

---

## Karar 3: BERT'i Dondurma (Freeze)

**Karar:** `freeze_bert=True`, `freeze_effnet=False` varsayılan.

**Kanıt:** `parser.set_defaults(freeze_bert=True, freeze_effnet=False)`

**Sonuç:** 116.2M toplam parametre → yalnızca 5.6M eğitilebilir.

**Tezde:** Bu strateji eğitim kararlılığını sağlamış, aşırı öğrenme riskini azaltmıştır.

---

## Karar 4: FastAPI + React Mimarisi

**Karar:** Backend FastAPI, frontend React + Vite.

**Gerekçe:** FastAPI, Python ML kütüphaneleriyle doğal entegrasyon; otomatik Swagger dokümantasyonu. React, zengin ekosistem, hot reload, i18n desteği. İkili, hem web hem masaüstü dağıtımına uygun.

---

## Karar 5: Çoklu Dil Desteği (i18n)

**Karar:** React kurulumundan hemen sonra i18n eklendi (`3b481f8`).

**Gerekçe:** Klinik kullanım için Türkçe şart; akademik sunum için İngilizce gerekli.

---

## Karar 6: Grad-CAM Açıklanabilirlik

**Karar:** Model tahminleri için Grad-CAM entegrasyonu.

**Gerekçe:** Klinik bağlamda kara kutu modeller kabul görmez. Grad-CAM tezin XAI boyutunu güçlendirir.

---

## Karar 7: Pseudo-Etiketleme ile Yarı Denetimli Öğrenme

**Karar:** Öğretmen-öğrenci pseudo-etiketleme yaklaşımı.

**Dezavantaj:** Öğretmen modelin hatası öğrenciye aktarılabilir (confirmation bias). Gerçek insan etiketlemesi kadar güvenilir değil.

---

## Karar 8: PyInstaller Masaüstü Paketleme

**Karar:** Python + React → bağımsız Windows `.exe`.

**Gerekçe:** Klinik ortamlarda internet bağlantısı veya kurulum yetkisi olmayabilir.

---

---

# 06 — Sistem Mimarisi Evrimi

## İlk Mimari (Kasım 2025)

```
CCDDA/
├── Dataset/Images/Education/test/Primary/   ← KIDO görüntüleri
├── checkpoints/
├── notebooks/
└── src/
    ├── data/ (dataset.py, transforms.py)
    ├── models/ (multimodal_effnet_bert.py)
    └── train/ (train_multimodal.py)
```

```
Görüntü → EfficientNet-B0 → [B, 1280] → img_proj (512)
                                                  ↓ Concat [1024]
Metin   → Türkçe BERT → [CLS] → [B, 768] → text_proj (512)
                                                  ↓
                                    Emotion Head (→2) + Gender Head (→2)
```

---

## Birinci Genişleme: Açıklanabilirlik + GUI (Kasım 2025)

```
src/
├── app/ (gui_multimodal.py, tk_app.py)
└── explain/ (gradcam.py, rule_based_explainer.py, predict_and_explain.py, ...)
```

Akış: Model → Grad-CAM → Rule-Based Explainer → Tkinter GUI

---

## İkinci Genişleme: Web + FastAPI (Şubat 2026)

```
CCDDA/
├── api_server.py          ← FastAPI (YENİ)
└── Web/                   ← React projesi (YENİ)
    └── src/
        ├── App.tsx
        └── locales/ (tr.json, en.json)
```

```
[React (port 3000)] → Vite proxy → [FastAPI (port 8000)]
                                           ↓
                                  [EfficientNet-B0 + BERT]
                                           ↓
                               [Rule-Based / LLM Explainer]
```

---

## Üçüncü Genişleme: Masaüstü Paketleme (Mart 2026)

```
CCDDA/
├── desktop_app.py         ← pywebview sarmalayıcı
├── desktop_app.spec       ← PyInstaller config
├── src/app_paths.py       ← Yol çözümleyici
├── build/, dist/          ← Derleme çıktıları
└── installer/             ← Inno Setup
```

Dağıtım seçenekleri: Web modu (React + FastAPI) | Masaüstü modu (PyInstaller .exe)

---

## Kritik Sıfırlama (Nisan 2026)

Kaldırılan: BERT tabanlı metin kodlayıcı, çok görevli AI, eski veri seti, eski checkpoint'ler.

Korunan: Web/ (React), desktop_app.py, api_server.py (503 modunda), src/explain/, src/app/

---

## Son Mimari (Mayıs 2026 — Aktif Geliştirme)

```
CCDDA/
├── Dataset/Images/
│   ├── Emotion_4Class/ (Anger/Fear/Happy/Sad)
│   ├── Emotion_Roboflow_DrawingFacialEmotions/
│   ├── Emotion_SigLIP_4Class/
│   └── huggingface/ (parquet)
├── out/
│   ├── highconf_pipeline/ (manifest_075: ~23K, manifest_085: ~19K)
│   └── consensus_pipeline/ (manifest_3of3: ~8.3K)
├── build_manifest_*.py, label_with_*.py
├── run_highconf_pipeline.py, run_consensus_pipeline.py
└── Web/ (korundu)
```

```
[Etiketsiz Görüntüler]
         ↓
[Öğretmen: EfficientNet-B3] → güven > 0.75 → [Pseudo-Etiketler]
         ↓ consensus filtresi
[Yüksek Kaliteli Manifest]
         ↓
[Öğrenci: EfficientNet-B3 (yeni eğitim)]
         ↓
[FastAPI /predict] → [React UI]
```

## Mimari Evrim Eksenleri

1. **Model:** Çok modlu → Tek modlu (görüntü-only)
2. **Arayüz:** Tkinter → React Web → PyInstaller masaüstü
3. **Veri:** Sabit küçük veri → Çok kaynaklı + pseudo-etiketleme

---

---

# 07 — Özellik Bazlı Gelişim

## Özellik 1: Çok Görevli Duygu + Cinsiyet Sınıflandırması

| | |
|---|---|
| İlk commit | `ec7d0f8` (30 Kasım 2025) |
| Son durum | `5311334`'de kaldırıldı |
| Sonuç | Duygu: %94.36, Cinsiyet: %77.12 |

AdamW optimizer, cosine LR scheduler. Emotion head ve gender head paylaşılan temsil üzerinden ayrı optimize edildi.

---

## Özellik 2: Grad-CAM Açıklanabilirlik

| | |
|---|---|
| İlk commit | `d494e7b` (30 Kasım 2025) |
| Son durum | `src/explain/gradcam.py` hâlâ mevcut |

PyTorch hook mekanizması ile son konvolüsyon katmanındaki aktivasyonlar ve gradyanlar yakalanır. Duygu ve cinsiyet için ayrı ısı haritaları üretilmektedir.

---

## Özellik 3: Kural Tabanlı + LLM Açıklama Sistemi

| | |
|---|---|
| İlk commit | `d494e7b` (kural tabanlı) |
| Son durum | `src/explain/llm_explainer.py` + `GITHUB_TOKEN` desteği |

Katmanlı yaklaşım: LLM varsa dinamik açıklama, yoksa şablon açıklama.

---

## Özellik 4: Tkinter Masaüstü GUI

| | |
|---|---|
| İlk commit | `d494e7b` |
| Son durum | `src/app/gui_multimodal.py` (394 satır) korunuyor |

---

## Özellik 5: React Web Arayüzü

`App.tsx` 555+ satıra ulaştı (7 commit boyunca büyüdü). Ana sayfa, analiz sayfası, hakkında sayfası (metrikleriyle) içeriyor.

---

## Özellik 6: FastAPI REST API

İlk versiyon 131 satır → büyük güncellemeyle 262 satır. `create_app()` factory patterni, `lifespan` bağlamı, `CCDDA_CHECKPOINT` env desteği.

---

## Özellik 7: Pseudo-Etiketleme Pipeline'ı

**High-Confidence:**
1. HuggingFace parquet → JPEG çıkarım
2. Tekilleştirilmiş envanter
3. Öğretmen modeli ile etiketleme
4. Güven eşiği filtresi (0.75/0.85)
5. Öğrenci modeli eğitimi

**Consensus:**
- 3 kaynak (Teacher-A/B/C)
- 3/3 mutabakat + %60 güven eşiği

---

## Özellik 8: Masaüstü Uygulama (PyInstaller + pywebview)

`desktop_app.py`: FastAPI'yi arka planda başlat → pywebview penceresi aç → kullanıcı kapatınca sunucuyu durdur.

---

## Özellik 9: Çok Dilli Arayüz (i18n)

4 commit boyunca büyüdü (+260 satır her dil dosyasına). Duygu etiketleri API'den gelen İngilizce değerleri kullanıcı diline çeviriyor.

---

---

# 08 — Hata Düzeltmeleri ve Refactoring

## Değişiklik 1: Kaydırılabilir Metin Alanı
**Commit:** `339a738` | **Tür:** UI iyileştirme
Tkinter `Text` widget + `Scrollbar`. Uzun açıklamalar artık tam okunabiliyor.

---

## Değişiklik 2: API Etiket Yerelleştirmesi
**Commit:** `ef0af36` (+109 satır) | **Tür:** Özellik genişletme
"Happiness" → Türkçe arayüzde "Mutluluk". API ve frontend tutarlılığı sağlandı.

---

## Değişiklik 3: API Yanıtına Açıklama Alanı
**Commit:** `1476c63` | **Tür:** API genişletmesi
`/predict` yanıtına `explanation` alanı eklendi.

---

## Değişiklik 4: Desktop Path Çözümleyicisi
**Commit:** `2a6895c` (`src/app_paths.py`) | **Tür:** Hata düzeltme
`sys.frozen` kontrolüyle geliştirme ve paketlenmiş ortam arasında yol farkı giderildi.

---

## Değişiklik 5: Kod Yapısı Refactoring
**Commit:** `72d8a7b` | **Tür:** Refactoring
Performans grafikleri `Web/public/about/`'a eklendi. `/about` sayfası model metrikleri gösteriyor.

---

## Değişiklik 6: label_with_model.py → v2
**Commit:** `73ff5de` | **Tür:** İteratif geliştirme
v2, v1'deki sorunları giderdi (kesin fark commit'ten belirlenemiyor).

---

## Değişiklik 7: GitIgnore Güncellemeleri
3 commit'te güncellendi (`b8b32b2`, `2a6895c`, `72d8a7b`). PyInstaller build dizinleri, `__pycache__` vb. eklendi.

---

## Değişiklik 8: API Server v1 → v2
**Commitler:** `08e1303` (131 satır) → `2a6895c` (262 satır)
`create_app()` factory patterni, `lifespan` bağlamı, env değişkenlerinden checkpoint yükleme.

---

---

# 09 — Test, Doğrulama ve Sınırlamalar

## Mevcut Test / Değerlendirme Scriptleri

| Dosya | Amaç | İlk Görüldüğü |
|---|---|---|
| `eval_test.py` | 4-sınıflı `ClinicalFusionClassifier` değerlendirmesi | `73ff5de` |
| `eval_tta.py` | Test-Time Augmentation değerlendirme | `73ff5de` |
| `src/eval/evaluate.py` | Temel değerlendirme modülü | Yeni sistem |
| `tools/run_report.py` | Eğitim + değerlendirme + rapor otomasyonu | `bab2958` |

Birim test (pytest vb.) veya CI/CD pipeline bulunmamaktadır.

---

## İlk Multimodal Modelin Kesin Değerlendirme Sonuçları

**Kaynak:** `artifacts/report_run/REPORT.md`

**Konfigürasyon:** 5 epoch, batch=16, LR=0.0001, AdamW, BERT frozen, KIDO (10.856 örnek)

| Küme | Boyut |
|---|---|
| Train | 7.843 |
| Validation | 1.383 |
| Test | 1.630 |

| Görev | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) | ROC-AUC |
|---|---|---|---|---|---|
| **Duygu** | **%94.36** | 0.9438 | 0.9436 | **0.9435** | **0.9866** |
| **Cinsiyet** | **%77.12** | 0.7637 | 0.7728 | **0.7658** | **0.8542** |

### Confusion Matrix — Duygu
| Gerçek \ Tahmin | Happiness | Sadness |
|---|---|---|
| Happiness | 759 (%93.1) | 56 (%6.9) |
| Sadness | 36 (%4.4) | 779 (%95.6) |

### Confusion Matrix — Cinsiyet
| Gerçek \ Tahmin | Female | Male |
|---|---|---|
| Female | 752 (%76.5) | 231 (%23.5) |
| Male | 142 (%17.4) | 505 (%62.6) |

---

## Pseudo-Etiket Kalite Kontrol Mekanizmaları

1. Güven eşiği filtreleri (0.75 / 0.85)
2. Görüntü hash'leme ile tekilleştirme
3. Sınıf dağılımı izleme (Counter)
4. Heldout test seti ayrımı
5. WeightedRandomSampler ile dengesizlik giderimi

---

## Sınırlamalar

1. **Otomatik test kapsamı yok** — birim test, entegrasyon test, CI/CD yok
2. **Değerlendirme verisi kalitesi bilinmiyor** — KIDO etiket kalitesi belgelenmemiş
3. **Pseudo-etiket güvenilirliği** — insan uzman etiketi değil; gürültü oranı bilinmiyor
4. **Sınıf dengesizliği** — cinsiyet: Female=983, Male=647
5. **Klinisyen değerlendirmesi yok** — gerçek klinik geçerlilik testi yapılmamış
6. **Genelleme belirsizliği** — farklı kültür/yaş gruplarında performans bilinmiyor
7. **Aktif geliştirme** — `/predict` hâlâ 503; yeni sistem henüz tamamlanmadı

---

---

# 10 — Tezde Kullanılabilecek Anlatım

> **Uyarı:** Bu paragraflar başlangıç noktasıdır. Tez yazarı kendi deneyimlediği bilgileri eklemeli ve sonuçları kesinleştirmelidir.

## Projenin Başlangıcı

Bu çalışma, çocukların el çizmesi resimlerinden duygusal durumun otomatik olarak tespit edilmesini amaçlamaktadır. Araştırmanın motivasyonu, klinik psikoloji pratiğinde yaygın kullanılan projektif çizim testlerinin değerlendirilme sürecindeki öznellik ve uzman bağımlılığıdır. Yapay zeka destekli bir analiz aracının, klinisyenlere nesnelleştirilmiş ve tekrar üretilebilir bir referans sunabileceği hipotezi temel alınmıştır.

Projenin veri tabanını KIDO veri seti oluşturmaktadır. Bu veri seti, Türk okul çocuklarına ait el çizmesi resimler içermekte olup dosya adlandırma şemasından her çizime ait okul, sınıf, öğrenci, cinsiyet ve duygu etiketleri çıkarılabilmektedir. Başlangıçta 10.856 etiketli örnek kullanılmıştır.

## İlk Prototipin Oluşturulması

Proje, Kasım 2025 sonunda çok modlu (multimodal) bir derin öğrenme sistemi olarak hayata geçirilmiştir. Bu ilk mimaride görüntü verisi EfficientNet-B0 ağıyla, metin verisi Türkçe BERT modeli (`dbmdz/bert-base-turkish-cased`) aracılığıyla kodlanmıştır. Her iki modaliteden elde edilen özellik vektörleri projeksiyon katmanlarıyla ortak bir 1024 boyutlu uzaya dönüştürülmüş ve birleştirilerek çok görevli bir sınıflandırıcıya aktarılmıştır. Sistem, duygu (Mutluluk/Üzüntü) ve cinsiyet (Kız/Erkek) sınıflandırmasını eş zamanlı gerçekleştirmiştir.

BERT parametreleri dondurulmuş, EfficientNet-B0 ince ayara tabi tutulmuştur. Bu asimetrik strateji, 116 milyon toplam parametreli modelde eğitilebilir parametre sayısını 5.6 milyona indirmiştir.

## Açıklanabilirlik Katmanının Geliştirilmesi

Klinik ortamlarda kabul için yorumlanabilirlik kritiktir. Grad-CAM görselleştirme modülü entegre edilerek modelin çizimin hangi bölgelerine odaklandığı ısı haritasıyla gösterilmektedir. Kural tabanlı açıklama üreticisi, model tahminini şablon açıklamalarla desteklemektedir. Sistem ayrıca LLM tabanlı dinamik açıklama üretimini de desteklemektedir.

## Arayüz Geliştirme Süreci

**İlk Prototip (Kasım 2025):** Tkinter GUI ile yerel masaüstü uygulaması geliştirilmiştir.

**Web Tabanlı Sistem (Şubat 2026):** React + TypeScript tabanlı web uygulamasına geçilmiştir. FastAPI ile `/predict` servisi oluşturulmuş; Türkçe ve İngilizce dil desteği eklenmiştir.

**Masaüstü Paketleme (Mart 2026):** PyInstaller ile bağımsız Windows paketi oluşturulmuştur.

## Mimari Yeniden Yapılanma

Nisan 2026'da çok modlu yaklaşım terk edilmiştir. BERT tabanlı bileşenler ve ilgili modüller devre dışı bırakılmıştır. Sınıflandırma hedefi iki sınıftan (Mutluluk/Üzüntü) dört sınıfa (Öfke, Korku, Mutluluk, Üzüntü) genişletilmiştir.

## Veri Büyütme: Yarı Denetimli Öğrenme

**Yüksek Güvenilirlikli Pseudo-Etiketleme:** Öğretmen modelin güven eşiğini (0.75/0.85) aşan tahminler yeni eğitim verisi olarak kullanılmaktadır (~19.000–23.000 ek örnek).

**Uzlaşma Tabanlı Etiketleme:** Üç bağımsız modelin mutabakatı şartı (~8.300 daha temiz örnek).

## Elde Edilen Sonuçlar

Daha önceki çok modlu sistem üzerinde duygu sınıflandırmasında %94.36 doğruluk oranı ve 0.9866 ROC-AUC elde edilmiştir. Yeni 4-sınıflı sistemin sonuçları henüz mevcut değildir.

## Etik Değerlendirme

Sistem klinik tanı aracı değildir. Değerlendirme raporundaki uyarıya göre çıktılar yalnızca araştırma ve karar-destek amaçlıdır; nihai yorum uzman profesyoneller tarafından yapılmalıdır.

## Sonuç

Bu proje, çocuk çizimi tabanlı duygu analizi alanında makine öğrenimi yöntemlerinin uygulanabilirliğini araştırmaktadır. Geliştirme süreci, çok modlu mimariden görüntü tabanlı mimariye, ikili sınıflandırmadan 4-sınıflı taksonomiye ve sınırlı veriden yarı denetimli öğrenmeye doğru iteratif bir evrimi yansıtmaktadır.

---

---

# 11 — Zaman Çizelgesi

| Tarih | Geliştirme Aşaması | İlgili Commitler | Açıklama |
|---|---|---|---|
| 2025-11-30 | Proje Kuruluşu + İlk Model | `ec7d0f8` | KIDO veri seti, eğitim scripti |
| 2025-11-30 | Multimodal Model Mimarisi | `b8b32b2` | EfficientNet-B0 + BERT |
| 2025-11-30 | GUI + Açıklanabilirlik | `d494e7b` | Tkinter, Grad-CAM, kural açıklayıcı |
| *2025-12 — 2026-01* | **Sessiz Dönem (~3 ay)** | — | Commitlenmemiş çalışmalar olabilir |
| 2026-02-22 | GUI İyileştirme | `339a738` | Kaydırılabilir metin |
| 2026-02-22 | React + i18n + FastAPI Sprint | `a04e560`–`bab2958` | 7 commit tek günde |
| 2026-03-12 | DOCX + Masaüstü + Refactoring | `16fa3d3`–`72d8a7b` | 3 commit |
| *2026-03 — 2026-04* | **Sessiz Dönem (~5 hafta)** | — | Karar değerlendirme |
| 2026-04-19 | Mimari Sıfırlama | `5311334` | Legacy AI kaldırıldı |
| 2026-04-20 | Yeni Plan | `fb8602a` | Backend V1 planı |
| *2026-04 — 2026-05* | **Sessiz Dönem (~2.5 hafta)** | — | Yeni sistem hazırlığı |
| 2026-05-08 | Yeni Altyapı | `dc64027` | .env, dataset düzenleme |
| 2026-05-10 | Pseudo-Etiketleme Scriptleri | `73ff5de` | Pipeline scriptleri |
| 2026-05-14 | Pipeline Çıktıları | `a846643` | Manifest CSV'leri |

```
2025-11     ████ [Proje başlangıcı: multimodal model + GUI + Grad-CAM]
2025-12     ░░░░ [Sessiz dönem]
2026-01     ░░░░ [Sessiz dönem]
2026-02-22  ████████ [YOĞUN SPRINT: React + FastAPI + i18n]
2026-03-12  ████ [Masaüstü + DOCX + Refactoring]
2026-03     ░░░░ [Sessiz dönem]
2026-04-19  ██ [SIFIRLAMA]
2026-04     ░░░░ [Sessiz dönem]
2026-05-08  █  [Ortam yapılandırması]
2026-05-10  ██ [Pseudo-etiketleme]
2026-05-14  █  [Pipeline çıktıları]
```

| Dönem | Commit | Yoğunluk |
|---|---|---|
| Kasım 2025 | 3 | Başlangıç |
| Aralık 2025 – Şubat 2026 | 1 | Sessiz dönem |
| 22 Şubat 2026 | 7 | **Çok yüksek (tek gün)** |
| 12 Mart 2026 | 3 | Orta |
| Nisan 2026 | 2 | Karar dönemi |
| Mayıs 2026 | 3 | Orta |

---

---

# 12 — Eksik Bilgiler ve Dürüst Notlar

## Net Olarak Çıkarılamayan Bilgiler

### 1. Projenin Tam Adı ve Tez Başlığı
`CCDDA` kısaltması dosya sisteminden. `Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx` başlığa işaret ediyor; kesin başlık tez yazarı tarafından belirtilmeli.

### 2. Metin Verisinin İçeriği
`master_emotion_gender.csv`'de `text_tr`, `text_en` sütunları var (`REPORT.md`'den); ancak içerikleri commit'lerden belirlenemiyor. Öğretmen/psikolog açıklamaları mı? Okul meta verisi mi?

### 3. Neden Çok Modlu Mimariden Vazgeçildi
Commit mesajı neden değil, ne yapıldığını söylüyor. Olası nedenler (hepsi tahmini): performans sorunu, metin kalitesi, tez danışmanı önerisi, araştırma kapsamı değişimi.

**Tez yazarı bu kararın nedenini kendi ifadesiyle belgelemelidir.**

### 4. Sessiz Dönemlerde Yapılanlar
3 sessiz dönem: ~3 ay + ~5 hafta + ~2.5 hafta. Bu dönemlerde ne yapıldığı bilinmiyor.

### 5. KIDO Veri Setinin Kaynağı ve Etiketleme Süreci
Nereden geldiği, kim etiketledi, hangi standartlarla sınıflara ayrıldı — **tez için kritik, mutlaka belgelenmeli.**

### 6. Klinik Geçerlilik
Bir uzman tarafından değerlendirilip değerlendirilmediği görünmüyor.

### 7. Yeni 4-Sınıflı Modelin Performansı
`eval_test.py` var ama değerlendirme sonuçları repo'da yok.

### 8. Pseudo-Etiket Eğitim Başarısı
Pipeline çıktıları var; ancak bu veriyle eğitilen öğrenci modelinin test performansı belgelenmemiş.

---

## Tahmine Dayalı Yorumlar

| Yorum | Kanıt Düzeyi |
|---|---|
| "Metin verisi Türkçe" | Zayıf (BERT seçiminden çıkarım) |
| "Tkinter'dan React'e geçiş mimari tercih" | Tahmini |
| "Sessiz dönemde yerel geliştirme yapıldı" | Tahmini |
| "Çok modlu yaklaşım performans sorunundan terk edildi" | Tahmini — gerçek neden bilinmiyor |
| "label_with_model_v2.py v1'deki hataları düzeltiyor" | Tahmini (isimlendirmeden) |

---

## Tez Yazarken Dikkat Edilmesi Gerekenler

1. **"Çok modlu model başarısız oldu" yazılmamalı** — sadece "geçiş yapıldı" denilebilir.
2. **%94 doğruluk dikkatli kullanılmalı** — 2-sınıflı dengeli görev, 5 epoch, frozen BERT. 4-sınıflı görevle analog kurmak yanıltıcı.
3. **~23.000 "pseudo-etiketli örnek" gerçek etiketli veri sayısı değildir** — net biçimde "pseudo-etiketlenmiş" olarak tanımlanmalı.
4. **Klinik doğrulama olmadığını belirtmek şart** — "araştırma prototipi", "klinik tanı aracı" değil.
5. **Cinsiyet sınıflandırması yeni sistemde hedef değil** — tezde değişiklik açıkça belirtilmeli.

---

## Öğrencinin Ekleyebileceği Bilgiler

- [ ] Projenin tam tez başlığı ve araştırma sorusu
- [ ] KIDO veri setinin kaynağı ve etiket üretim süreci
- [ ] Multimodal modelden vazgeçilmesinin gerçek nedeni
- [ ] Tez danışmanının yönlendirmeleri
- [ ] Sessiz dönemlerdeki çalışmalar (literatür, görüşmeler, vb.)
- [ ] Grad-CAM görsellerinin klinik değerlendirmesi
- [ ] Yeni 4-sınıflı modelin eğitim ve test sonuçları
- [ ] Kullanıcı testi veya klinik değerlendirme sonuçları
- [ ] Etik kurul onayı durumu (çocuk verisi)
- [ ] HuggingFace ve Roboflow veri seti lisans durumu

---

## Commit Mesajı Kalitesi

**İyi mesajlar:** `feat: initialize React project...`, `feat: add desktop application...`, `chore: remove legacy dataset...`

**Yetersiz mesajlar:** `Ağırlık düzenleme`, `Ezber cümleler`, `Save: push all local changes`, `Auto-commit`

Yetersiz mesajlı commit'ler diff içeriğinden analiz edildi; bu bölümlerdeki yorumlar tahmine dayalıdır.

---

---

# README — Klasör Rehberi

Bu klasör, CCDDA projesinin geliştirme sürecini Git commit geçmişi, kaynak kodu ve mevcut dosya yapısından yeniden oluşturan akademik dokümantasyon içermektedir.

## Bu Dokümantasyonun Amacı

- Tez yazım sürecine kronolojik geliştirme anlatısı sağlamak
- Teknik kararların ve gerekçelerinin belgelenmesi
- Karşılaşılan problemlerin ve çözüm yaklaşımlarının kayıt altına alınması
- Tezde kullanılabilecek hazır akademik paragraflar sunmak
- Belirsiz veya tahmini bilgileri dürüstçe işaretlemek

## Kaynaklar

Git commit geçmişi, commit diff'leri, mevcut dosya yapısı ve kaynak kodu, `artifacts/report_run/REPORT.md`, `api_server.py` ve pipeline scriptleri.

## Bilginin Güvenilirlik Düzeyleri

**Kesin:** Commit diff'lerinde, kaynak kodunda veya raporlarda açıkça görülen bilgiler.

**Tahmini:** "Muhtemelen", "olasılıkla", "tahminen" gibi ifadelerle işaretlenmiş yorumlar.

**Bilinmeyen:** `12_eksik_bilgiler_ve_durust_notlar.md`'de listelenenler — tez yazarı tarafından tamamlanmalı.

## Önemli Uyarı

Bu dokümantasyon commit geçmişini yorumlayan bir analizdir. Tez yazarının bizzat deneyimlediği ancak commit'lere yansımayan süreçler bu dosyalarda yer almamaktadır. Bu dokümantasyonu başlangıç noktası olarak kullanın; kendi bilgi ve deneyiminizle zenginleştirin.

---

*Bu dosya (13_tam_dokumantasyon_birlestirme.md), `docs/thesis-development/` klasöründeki 00–12 numaralı dosyaların ve README'nin içeriğini tek bir belgede birleştirir. Diğer dosyalar silinmemiştir.*

*Oluşturulma: Mayıs 2026 | Claude Code tarafından Git geçmişi analizi yoluyla üretilmiştir.*
