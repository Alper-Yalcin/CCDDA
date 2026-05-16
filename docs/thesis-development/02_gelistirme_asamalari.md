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
