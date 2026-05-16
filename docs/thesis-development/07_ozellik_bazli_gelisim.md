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
`gui_multimodal.py`, 394 satırlık kapsamlı bir Tkinter uygulamasıdır. Dosya boyutundan ve adından, görüntü yükleme, model çalıştırma ve sonuç gösterimi işlevlerini içerdiği anlaşılmaktadır. `tk_app.py` daha sade bir wrapper olabilir.

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
`App.tsx` birden fazla commit sonunda 555+ satıra ulaşmıştır. Uygulama muhtemelen şu ekranları içermektedir:
- Ana sayfa / karşılama
- Analiz sayfası (görüntü yükleme + tahmin)
- Hakkında sayfası (model metrikleri, grafikler)

Dil seçimi kullanıcı tarafından değiştirilebilmektedir.

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
