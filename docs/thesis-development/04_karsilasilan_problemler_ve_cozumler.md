# 04 — Karşılaşılan Problemler ve Çözümler

Bu dosya, commit geçmişi, kod değişimleri ve mevcut dosya yapısından çıkarılabilen teknik problemleri ve uygulanan çözümleri belgeler. Kesin neden belirtilemeyen durumlarda yoruma dayalı ifadeler kullanılmıştır.

---

## Problem 1: Metin Açıklamaları Statik Kalmaktaydı ("Ezber Cümleler")

### Problem Nasıl Anlaşılıyor?
`d494e7b` commitinin mesajı "Ezber cümleler ve GUI eklendi" ifadesini içermektedir. `src/explain/rule_based_explainer.py` dosyası, olasılıkla önceden belirlenmiş şablon cümleler içermektedir. "Ezber cümleler" ifadesi bu şablonların sabit ve tekrar eden bir yapıda olduğuna işaret etmektedir.

### İlgili Commitler
- `d494e7b` — kural tabanlı açıklayıcı eklendi
- `08e1303`, `1476c63`, `ef0af36` — API'ye açıklama alanı eklendi ve zenginleştirildi

### Uygulanan Çözüm
Hem kural tabanlı açıklayıcı (`rule_based_explainer.py`) korunurken hem de daha dinamik açıklama üretimi API katmanına eklendi. `api_server.py` içinde bir LLM (büyük dil modeli) entegrasyonu için "GITHUB_TOKEN" gibi ortam değişkeni desteği de görülmektedir; bu, dinamik açıklama üretimi için harici bir LLM'ye sorgu atılmasına olanak tanıyor olabilir. Mevcut `src/explain/llm_explainer.py` dosyası bu amaçla yazılmış görünmektedir.

### Çözümün Etkisi
Açıklama sistemi katmanlı hale geldi: LLM mevcut değilse kural tabanlı açıklama devreye giriyor; LLM mevcutsa daha zengin ve bağlamsal açıklama üretiliyor.

### Tezde Kullanılabilecek Açıklama
Sistemin açıklanabilirlik katmanı kural tabanlı bir fallback mekanizmasıyla desteklenmiştir. Bu yaklaşım, yapay zeka modellerinin "kara kutu" sorununa karşı ilk cevabı oluşturmakta; Grad-CAM görselleştirmesiyle birlikte çok katmanlı bir açıklanabilirlik çerçevesi sunmaktadır.

---

## Problem 2: Tkinter GUI'de Uzun Açıklamaların Görüntülenememesi

### Problem Nasıl Anlaşılıyor?
`339a738` commitinin mesajı "Add scrollable text widget for explanation and refactor explanation generation" içermektedir. Bu, kaydırma olmadan uzun açıklamaların tam görüntülenemediğine işaret etmektedir.

### İlgili Commitler
- `339a738` — kaydırılabilir metin alanı eklendi

### Uygulanan Çözüm
Tkinter'da `Text` widget'ı ile kaydırma çubuğu (`Scrollbar`) birleştirilerek açıklama alanı kaydırılabilir hale getirildi.

### Çözümün Etkisi
Kullanıcı artık tam açıklama metnini okuyabilmektedir. Aynı commit açıklama üretim mantığını da yeniden düzenlemiş; bu, açıklamanın artık daha uzun veya yapılandırılmış metin ürettiğini gösteriyor olabilir.

### Tezde Kullanılabilecek Açıklama
Prototip değerlendirme sürecinde kullanıcı arayüzünde işlevsel eksiklikler tespit edilmiş ve bu eksiklikler iteratif iyileştirmelerle giderilmiştir.

---

## Problem 3: Frontend ve Backend Arasındaki İletişim

### Problem Nasıl Anlaşılıyor?
`08e1303` commitinde `Web/vite.config.ts` değiştirilmiştir. Vite yapılandırma dosyasındaki değişiklik genellikle proxy ayarlarına yapılır; bu, React dev sunucusunun FastAPI arka ucuna istek yönlendirmesi için gereklidir.

### İlgili Commitler
- `08e1303` — vite.config.ts güncellendi, FastAPI eklendi

### Uygulanan Çözüm
Vite proxy yapılandırması eklenerek React dev ortamındaki `/api` yoluna gelen istekler FastAPI sunucusuna (`localhost:8000`) yönlendirildi. CORS middleware de FastAPI'ye eklendi.

### Çözümün Etkisi
Frontend ve backend ayrı portlarda çalışabilir hale geldi (React: 3000, FastAPI: 8000) ve CORS hataları ortadan kalktı.

### Tezde Kullanılabilecek Açıklama
İstemci-sunucu mimarisi kurulumunda çapraz kaynaklı istek (CORS) sorunları giderilmiş ve geliştirme ortamı için proxy yapılandırması yapılmıştır.

---

## Problem 4: Eski AI Yığınının Sürdürülemezliği

### Problem Nasıl Anlaşılıyor?
`5311334` commit mesajı: "chore: remove legacy dataset and reset old AI stack". README'de şu ifade yer almaktadır: "eski multimodal AI hattı bu repodan temizlendi" ve "legacy AI giris noktalari bilincli olarak devre disi birakildi".

### İlgili Commitler
- `5311334` — eski yığın tamamen kaldırıldı

### Uygulanan Çözüm
Radikal bir temizlik yapıldı. BERT tabanlı bileşenler, eski eğitim verileri ve eski model entegrasyon noktaları kaldırıldı. API `/predict` endpoint'i geçici olarak `503` döndürecek şekilde devre dışı bırakıldı. Yeni sistem için temiz bir başlangıç noktası oluşturuldu.

### Çözümün Etkisi
Repo daha az karmaşık hale geldi. Yeni geliştirme yönü (4-sınıflı görüntü-only) netleşti. Ancak eski sistemin bıraktığı çalışan bir model geçici olarak ortadan kalktı.

### Tezde Kullanılabilecek Açıklama
Geliştirme sürecinde mimari bir yeniden yapılanmaya gidilmiş; mevcut çok modlu sistemin karmaşıklığı ve akademik odağın yeniden tanımlanması doğrultusunda sistem, daha sade ve odaklı bir görüntü tabanlı mimariye dönüştürülmüştür.

---

## Problem 5: Etiketlenmiş Veri Kıtlığı

### Problem Nasıl Anlaşılıyor?
Beş farklı manifest scripti (`build_manifest_*.py`) ve iki büyük pseudo-etiketleme pipeline'ı (`run_highconf_pipeline.py`, `run_consensus_pipeline.py`) mevcut olması, etiketli veri yetersizliğinin temel bir sorun olduğunu göstermektedir. HuggingFace parquet veri kümesi eklenmesi de bu sorunu aşmak için harici kaynağa başvurulduğunu göstermektedir.

### İlgili Commitler
- `73ff5de` — pseudo-etiketleme scriptleri eklendi
- `a846643` — pipeline çıktıları üretildi

### Uygulanan Çözüm
Üç katmanlı veri büyütme yaklaşımı:
1. **Harici veri entegrasyonu**: HuggingFace parquet ve Roboflow Drawing Facial Emotions veri seti
2. **Yüksek güvenilirlikli pseudo-etiketleme**: Öğretmen modelin ≥0.75 veya ≥0.85 güvenle tahmin ettiği örnekler yeni eğitim verisi olarak kullanılıyor
3. **Consensus etiketleme**: 3 farklı modelin (HuggingFace VLM, Ollama, mevcut model) aynı etiketi ürettiği örnekler seçiliyor

### Çözümün Etkisi
`out/highconf_pipeline/` çıktısına göre `manifest_highconf_075.csv` ~23,000 örnek, `manifest_highconf_085.csv` ~19,000 örnek içermektedir. Bu, orijinal KIDO veri setinin çok üzerinde bir veri büyütmesini temsil etmektedir.

### Tezde Kullanılabilecek Açıklama
Derin öğrenme modellerinin yüksek başarı oranına ulaşabilmesi için büyük miktarda etiketli veriye ihtiyaç duyduğu bilinmektedir. Bu projede, sınırlı insan etiketli verinin yarattığı kısıtı aşmak amacıyla yarı denetimli öğrenme yaklaşımı benimsenmiş; pseudo-etiketleme ile veri kümesi genişletilmiştir.

---

## Problem 6: Masaüstü Dağıtımı (Paketleme)

### Problem Nasıl Anlaşılıyor?
`2a6895c` commitinin detaylı mesajı, masaüstü uygulamanın birden fazla bileşeninin (PyInstaller spec, Inno Setup, build script, `app_paths.py`) aynı anda eklenmesi gerektiğini ortaya koymaktadır. `app_paths.py` özellikle paketlenmiş uygulamada dosya yollarının doğru çözümlenmesi için eklenmiştir — bu, PyInstaller paketlerinde yaygın bir sorundur.

### İlgili Commitler
- `2a6895c` — masaüstü uygulama altyapısı

### Uygulanan Çözüm
`src/app_paths.py` ile geliştirme ve paketlenmiş ortamlar için dosya yolları dinamik olarak çözümleniyor. PyInstaller spec dosyasında gerekli tüm veri dosyaları (web statik dosyalar, model ağırlıkları) dahil edildi.

### Çözümün Etkisi
Uygulama tek bir `.exe` dosyasına ya da kurulum paketine dönüştürülebilir hale geldi.

### Tezde Kullanılabilecek Açıklama
Sistemin bağımsız masaüstü uygulaması olarak dağıtılabilmesi için paketleme altyapısı oluşturulmuş; kurulum gerektirmeyen çalıştırılabilir format sağlanmıştır.

---

## Problem 7: Model Değerlendirme Metrikleri ve Raporlama

### Problem Nasıl Anlaşılıyor?
`bab2958` commiti özellikle bir "rapor çalıştırıcı" (`run_report.py`) ve konfigürasyon dosyası (`run_args.json`) eklemiştir. Bu, standart bir değerlendirme sürecinin olmadığını ve her seferinde ayrı ayrı metrik hesaplama yapıldığını göstermektedir. İlk modelin değerlendirme raporu (`artifacts/report_run/REPORT.md`) mevcut olup önemli metrikler içermektedir.

### İlgili Commitler
- `bab2958` — raporlama altyapısı

### Uygulanan Çözüm
Eğitim, değerlendirme ve rapor üretimini tek bir komutla çalıştıran otomasyon scripti yazıldı. Çıktılar:
- Confusion matrix görseli
- ROC eğrisi görseli
- Sayısal metrikler tablosu (accuracy, precision, recall, F1)

**Elde Edilen Sonuçlar (İlk Model):**
| Görev | Accuracy | F1 (macro) | ROC-AUC |
|---|---|---|---|
| Duygu (2 sınıf) | %94.36 | 0.9435 | 0.9866 |
| Cinsiyet (2 sınıf) | %77.12 | 0.7658 | 0.8542 |

### Çözümün Etkisi
Tekrar üretilebilir, belgelenmiş bir değerlendirme süreci oluşturuldu. Bu metrikler tezde doğrudan referans verilebilir.

### Tezde Kullanılabilecek Açıklama
İlk multimodal model, 10.856 örneklik KIDO veri seti üzerinde değerlendirilmiş ve duygu sınıflandırmasında %94.36 doğruluk oranına, ROC-AUC değeri 0.987'ye ulaşmıştır. Cinsiyet sınıflandırması ise %77.12 doğrulukla daha zor bir görev olarak öne çıkmıştır.
