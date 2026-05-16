# 02 — Geliştirme Aşamaları

Bu dosya, commit geçmişinden çıkarılan geliştirme sürecini anlamlı aşamalara gruplamaktadır. Aşamalar kronolojik sıradadır ve her biri ilgili commit ID'leri ile belgelenmiştir.

---

# Aşama 1: Proje Kurulumu ve İlk Çok Modlu Model

**Dönem:** Kasım 2025 (30 Kasım 2025)
**İlgili Commitler:** `ec7d0f8`, `b8b32b2`, `d494e7b`

## Yapılan İşler

- KIDO veri seti (çocuk çizimleri) projeye dahil edildi. Görüntüler `Dataset/Images/Education/test/Primary/` altında düzenlendi.
- Veri dosya adlandırma formatı belirlendi: `[okul_id]-[sınıf]-[öğrenci_id]-[cinsiyet]-[duygu].jpg` (örn. `101-1A-369-F-H.jpg`)
- Çok modlu sinir ağı mimarisi tasarlandı:
  - **Görüntü kodlayıcı:** EfficientNet-B0 (ImageNet ağırlıklarıyla)
  - **Metin kodlayıcı:** `dbmdz/bert-base-turkish-cased` (Türkçe BERT)
  - **Birleştirme:** Projeksiyon katmanlarıyla gömme boyutu 512'ye indirgendi, sonra concat
  - **Çıkış kafaları:** Duygu kafası (Happiness/Sadness, 2 sınıf) + Cinsiyet kafası (Female/Male, 2 sınıf)
- EfficientNet varsayılan olarak eğitilebilir, BERT varsayılan olarak dondurulmuş (freeze) olarak başlatıldı.
- Tkinter tabanlı masaüstü GUI oluşturuldu.
- Grad-CAM açıklanabilirlik modülü geliştirildi — modelin görüntünün hangi bölgesine odaklandığı görselleştiriliyor.
- Kural tabanlı açıklayıcı (`rule_based_explainer.py`) ve metin tabanlı açıklayıcı (`text_explain.py`) eklendi.
- Bir harici API (muhtemelen görüntü analiz amaçlı) için `perception_api.py` oluşturuldu.

## Teknik Değerlendirme

Bu aşamanın en dikkat çekici özelliği, projenin başlangıcından itibaren **iki ayrı sınıflandırma görevini** (duygu + cinsiyet) aynı anda hedeflemesidir. Bu çok görevli (multi-task) öğrenme yaklaşımı, hem veri etiketlemesinin de zaten bu iki boyutu içerdiğini (dosya adı şemasından anlaşılmaktadır) hem de araştırmacının iki boyuttaki sinyali birden yakalamayı planladığını göstermektedir.

BERT'in dondurulmuş başlatılması standart bir transfer öğrenimi stratejisidir: büyük dil modelinin ağırlıklarını eğitim başında sabit tutmak, özellikle küçük veri setlerinde aşırı öğrenmeyi azaltır.

Commit mesajındaki "ezber cümleler" ifadesi, kural tabanlı açıklayıcıda kullanılan önceden tanımlı açıklama şablonlarına işaret etmektedir. Bu yaklaşım, LLM tabanlı açıklamadan daha belirleyici (deterministik) bir alternatiftir.

## Tezde Kullanılabilecek Anlatım

Projenin ilk aşamasında çok görevli bir derin öğrenme mimarisi benimsenmiştir. Bu mimaride görüntü bilgisi EfficientNet-B0 ile, metin bilgisi ise Türkçe BERT modeliyle kodlanmış; her iki modaliteden elde edilen özellikler birleştirilmiş ve iki bağımsız sınıflandırma kafasına aktarılmıştır. Açıklanabilirlik ön planda tutulmuş, Grad-CAM görselleştirmesi ve kural tabanlı metin açıklamaları sisteme entegre edilmiştir.

---

# Aşama 2: Tkinter GUI Olgunlaştırma (Ara Dönem)

**Dönem:** Kasım 2025 – Şubat 2026
**İlgili Commitler:** `339a738`

## Yapılan İşler

- Tkinter GUI'de açıklama metni için kaydırılabilir metin alanı eklendi.
- Açıklama üretim mantığı yeniden düzenlendi.

## Teknik Değerlendirme

Bu tek commit, yaklaşık 3 aylık bir sessizlikten sonra gelmiştir. Bu süreçte yerel geliştirme yapıldığı ancak commitlenmediği tahmin edilmektedir. Yapılan değişiklik küçük ama işlevsel: kullanıcı açıklamayı görmek için kaydırma yapabilsin diye UI iyileştirilmiş.

## Tezde Kullanılabilecek Anlatım

İlk prototip aşamasında Tkinter kütüphanesi ile yerel masaüstü arayüzü geliştirilmiş; kullanıcı deneyimi geri bildirimleri doğrultusunda kaydırılabilir açıklama alanı gibi UI iyileştirmeleri yapılmıştır.

---

# Aşama 3: Web Arayüzü ve FastAPI Backend'e Geçiş

**Dönem:** 22 Şubat 2026 (yoğun tek gün)
**İlgili Commitler:** `a04e560`, `3b481f8`, `08e1303`, `1476c63`, `ef0af36`, `bab2958`

## Yapılan İşler

- **Mimari geçiş:** Tkinter masaüstü uygulamasından React web uygulamasına geçildi.
- React + Vite + TypeScript + Tailwind CSS ile web projesi kuruldu.
- Türkçe/İngilizce çoklu dil desteği (i18next) eklendi.
- FastAPI tabanlı REST API arka ucu (`api_server.py`) oluşturuldu:
  - `/health` endpoint'i
  - `/predict` endpoint'i: resim + metin girişi alıp model çıktısı + açıklama döndürüyor
  - CORS middleware (React dev sunucusuyla iletişim için)
- API yanıtına açıklama (explanation) alanı eklendi.
- Duygu ve cinsiyet etiketleri için dil bazlı yerelleştirme desteği API'ye entegre edildi.
- Eğitim, değerlendirme ve raporlama otomasyonu (`run_report.py`) eklendi.
- Confusion matrix ve ROC eğrisi grafikleri üretildi.

## Teknik Değerlendirme

Bu aşama, tek bir gün içinde gerçekleştirilmiş yoğun bir geliştirme sprintidir (7 commit, 22 Şubat 2026). Tkinter'dan React'e geçiş önemli bir mimari karardır; web tabanlı arayüz daha geniş erişilebilirlik, daha kolay güncelleme ve daha modern kullanıcı deneyimi sağlar.

Vite proxy yapılandırması güncellenerek React dev ortamı FastAPI arka ucuna yönlendirilmiştir — bu standart bir full-stack geliştirme düzenidir.

Raporlama altyapısının eklenmesi (confusion matrix, ROC), projenin akademik değerlendirme boyutunu ciddiye aldığını göstermektedir.

## Tezde Kullanılabilecek Anlatım

Sistemin kullanılabilirlik ve erişilebilirlik gereksinimlerini karşılamak amacıyla yerel masaüstü arayüzünden modern web teknolojilerine geçiş yapılmıştır. React ve FastAPI kullanılarak istemci-sunucu mimarisi oluşturulmuş; çok dilli arayüz desteği ile sistem hem Türkçe hem İngilizce kullanıcıya hitap edebilir hale getirilmiştir.

---

# Aşama 4: Masaüstü Paketleme ve Raporlama

**Dönem:** 12 Mart 2026
**İlgili Commitler:** `16fa3d3`, `2a6895c`, `72d8a7b`

## Yapılan İşler

- Markdown'dan DOCX formatına dönüştürme scripti (`build_report_docx.py`) geliştirildi. DOCX şablonu referans alınarak başlıklar, tablolar, listeler ve görseller dönüştürülüyor.
- Tez belgesi şablonu (`Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx`) repo'ya eklendi.
- FastAPI + React'i saran masaüstü uygulaması (`desktop_app.py`) oluşturuldu:
  - Uygulama başladığında FastAPI sunucu arka planda başlatılıyor.
  - pywebview ile yerel tarayıcı penceresi açılıyor.
- PyInstaller spec dosyası (`desktop_app.spec`) yapılandırıldı.
- Windows kurulum paketi için Inno Setup scripti oluşturuldu.
- Derleme otomasyonu için PowerShell scripti (`build_desktop.ps1`) yazıldı.
- Web uygulamasının `/about` sayfasına performans grafikleri eklendi.
- Kod yapısı okunabilirlik açısından yeniden düzenlendi.

## Teknik Değerlendirme

Bu aşama projenin "dağıtım" (deployment) boyutunu kapsamaktadır. PyInstaller + pywebview kombinasyonu, bir Python uygulamasını kendi içinde tüm bağımlılıklarını barındıran çalıştırılabilir bir masaüstü uygulamasına dönüştürmek için yaygın kullanılan bir yaklaşımdır.

Hem web uygulaması hem masaüstü paket olarak dağıtım seçeneğinin korunması, farklı kullanıcı senaryolarını (klinik ortam, araştırma, demo) karşılamayı hedeflemiş olabilir.

## Tezde Kullanılabilecek Anlatım

Sistemin hem web tarayıcısından hem de bağımsız masaüstü uygulaması olarak çalışabilmesi sağlanmıştır. PyInstaller ile Windows çalıştırılabilir paketi oluşturulmuş; bu sayede internet bağlantısı gerektirmeyen klinik ortamlarda kullanım mümkün hale getirilmiştir.

---

# Aşama 5: Kritik Mimari Sıfırlama

**Dönem:** 19–20 Nisan 2026
**İlgili Commitler:** `5311334`, `fb8602a`

## Yapılan İşler

- **Eski AI yığını tamamen kaldırıldı:**
  - BERT tabanlı metin kodlayıcı
  - Çok modlu (multimodal) füzyon katmanı
  - Eski eğitim veri seti
  - Eski model checkpoint'leri ve explainability modülleri
- README yeniden yazılarak projenin yeni yönü açıklandı.
- Backend V1 için mikro-sprint yürütme planı oluşturuldu.

## Teknik Değerlendirme

Bu, projenin en önemli dönüm noktasıdır. README'deki açıklama (Nisan 2026 tarihli, `api_server.py` yorumundan okunmuştur) bu kararın gerekçesini özetlemektedir: eski yapı "emotion + gender çok görevli sınıflandırma + BERT tabanlı multimodal akış" içeriyordu; yeni hedef ise "yeni etiketli görüntü-only veriyle sıfırdan kurulacak yeni AI sistemi"dir.

Bu geçişin nedeni commit geçmişinde açıkça belirtilmemiştir. Olası gerekçeler:
- Çok modlu yaklaşımın beklenen performansı sağlamamış olması
- Metin verisinin kalitesi veya tutarlılığıyla ilgili sorunlar
- Akademik odağın daraltılması (tez kapsamı)
- Yeni 4-sınıflı duygu taksonomisine geçiş gerekliliği (ikili sınıflandırmadan Anger/Fear/Happiness/Sadness'a)

## Tezde Kullanılabilecek Anlatım

Geliştirme sürecinde, çok modlu yaklaşımdan vazgeçilerek yalnızca görüntü tabanlı bir mimariye geçilmesine karar verilmiştir. Bu karar, sınıflandırma hedefinin de iki sınıftan dört sınıfa (Anger, Fear, Happiness, Sadness) genişletilmesiyle eş zamanlı alınmıştır. Böylece sistem daha net ve ölçülebilir bir araştırma hedefine yönlendirilmiştir.

---

# Aşama 6: Yeni Veri Hattı — Pseudo-Etiketleme

**Dönem:** Mayıs 2026 (8–14 Mayıs 2026)
**İlgili Commitler:** `dc64027`, `73ff5de`, `a846643`

## Yapılan İşler

- Ortam değişkeni altyapısı (`env`, `.env.example`) kuruldu.
- Yeni 4-sınıflı veri kümesi yapılandırması oluşturuldu: `Dataset/Images/Emotion_4Class/` (Anger/Fear/Happy/Sad)
- Birden fazla pseudo-etiketleme scripti geliştirildi:
  - `label_with_hf.py`: HuggingFace modelleriyle etiketleme
  - `label_with_ollama.py`: Ollama (yerel) LLM ile etiketleme
  - `label_with_model.py` / `label_with_model_v2.py`: Mevcut eğitilmiş model ile etiketleme
  - `ollama_annotate.py`: Ollama annotasyon scripti
- Veri manifesti oluşturma scriptleri geliştirildi:
  - `build_manifest_kido.py`
  - `build_manifest_expanded.py`
  - `build_manifest_v2.py`
  - `build_manifest_final.py`
  - `build_manifest_qwen.py`
- İki büyük pipeline oluşturuldu:
  - `run_highconf_pipeline.py`: Yüksek güvenilirlikli pseudo-etiketleme (güven eşiği: 0.75 / 0.85)
  - `run_consensus_pipeline.py`: Çoklu model uzlaşmasına dayalı etiketleme (3/3 model mutabakatı)
- Pipeline çıktıları (`out/highconf_pipeline/`, `out/consensus_pipeline/`) üretildi ve repo'ya eklendi.

## Teknik Değerlendirme

Bu aşama, etiketli veri kıtlığı sorununa yönelik **öğretmen-öğrenci (teacher-student) öğrenme** yaklaşımını yansıtmaktadır. Mevcut eğitilmiş model ("öğretmen") etiketsiz görüntüleri tahmin ediyor; yüksek güvenilirlikli tahminler yeni eğitim verisi olarak kullanılıyor ("öğrenci" modeli bu veriyle eğitilecek).

İkinci yaklaşım olan "consensus pipeline" ise birden fazla farklı modelin (Qwen VL, HuggingFace modelleri, yerel öğretmen) aynı görüntü için aynı etiketi vermesini şart koşuyor (3/3 mutabakat). Bu, gürültülü pseudo-etiketleme çıktılarını filtrelemek için güçlü bir yöntemdir.

HuggingFace parquet veri kümesinin varlığı (`Dataset/huggingface/`) ve `run_highconf_pipeline.py` içindeki ayıklama kodu, projenin çevrimiçi çizim/duygu veri kümelerini de dahil etmeye çalıştığını göstermektedir.

## Tezde Kullanılabilecek Anlatım

Veri kıtlığı sorununu aşmak amacıyla pseudo-etiketleme (yarı denetimli öğrenme) yaklaşımı benimsenmiştir. Bu yaklaşımda önceden eğitilmiş bir öğretmen modeli, etiketsiz görüntüleri sınıflandırmakta; belirli bir güven eşiğini (0.75 ve 0.85) aşan tahminler yeni eğitim verisi olarak değerlendirilmektedir. Ek olarak, birden fazla modelin mutabakatını gerektiren uzlaşma (consensus) tabanlı etiketleme stratejisi ile etiket gürültüsü azaltılmıştır.
