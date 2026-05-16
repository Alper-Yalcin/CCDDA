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
`2a6895c`'de eklenen 9 satır muhtemelen PyInstaller derleme dizinleri (`build/`, `dist/`), pywebview geçici dosyaları veya `__pycache__` gibi klasörleri kapsıyor. `72d8a7b`'de eklenen 4 satır masaüstü paketlemeyle ilgili ek dizinleri içeriyor olabilir.

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
