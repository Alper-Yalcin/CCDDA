# 12 — Eksik Bilgiler ve Dürüst Notlar

Bu dosya, Git geçmişinden net olarak çıkarılamayan bilgileri ve tez yazarına yönelik dürüst uyarıları içermektedir. Bu dosya, tezde yanlış veya abartılı ifade kullanılmasının önüne geçmek amacıyla hazırlanmıştır.

---

# Net Olarak Çıkarılamayan Bilgiler

## 1. Projenin Tam Adı ve Tez Başlığı

Git commit'leri ve kaynak kodunda projenin resmi adı açıkça belirtilmemiştir. `CCDDA` kısaltması dosya sisteminden gelmektedir. `Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx` dosyası, tez başlığının "Çocuk Çizimlerinden Duygu Analizi" veya benzeri olduğuna işaret etmektedir; ancak kesin başlık tez yazarı tarafından belirtilmelidir.

## 2. Metin Verisinin İçeriği (İlk Çok Modlu Model)

Multimodal modelde BERT kodlayıcısına verilen "metin" verisinin tam olarak ne olduğu kesin tespit edilememiştir. Dosya adı şemasından cinsiyet ve duygu zaten bilinmektedir; bu durumda metin verisi şunlardan biri olabilir:
- Öğretmen veya psikolog tarafından yazılmış çizim açıklamaları
- Okul/sınıf meta verileri
- Başka bir metin kaynağı

`master_emotion_gender.csv` dosyasına ve `text_tr`, `text_en` sütunlarına yapılan referanslar mevcuttur (`REPORT.md`'den); ancak bu sütunların içeriği commit'lerden belirlenemiyor.

## 3. Neden Çok Modlu Mimariden Vazgeçildi

`5311334` commit mesajı ("chore: remove legacy dataset and reset old AI stack") ve README güncellemesi bu kararın gerçekleştirildiğini belgeler; ancak kararın gerekçesi açıkça ifade edilmemiştir. Olası nedenler (hepsi tahmini):
- Modelin yeterli performans göstermemesi
- Metin verisinin tutarsızlığı veya kalite sorunları
- Tez danışmanı önerisi
- Araştırma kapsamının yeniden tanımlanması
- Yeni 4-sınıflı hedefle multimodal yaklaşımın uyumsuzluğu

**Tez yazarı bu kararın nedenini kendi ifadesiyle belgelemelidir.**

## 4. Model Eğitim Sonuçlarının Nasıl Değerlendirildiği

Raporlama altyapısı mevcut olmakla birlikte, sonuçların tez danışmanına sunulup sunulmadığı, klinisyenlerle değerlendirilip değerlendirilmediği ya da yinelemeli iyileştirmeye yol açıp açmadığı commit geçmişinde görünmemektedir.

## 5. Sessiz Dönemlerde Yapılanlar

Üç sessiz dönem tespit edilmiştir:
- Kasım 2025 sonu – Şubat 2026: ~3 ay
- Mart 2026 sonu – Nisan 2026: ~5 hafta
- Nisan 2026 ortası – Mayıs 2026: ~2.5 hafta

Bu dönemlerde neler yapıldığı (literatür tarama, danışman görüşmesi, yerel kodlama, veri toplama vb.) bilinmemektedir.

## 6. KIDO Veri Setinin Kaynağı ve Etiketleme Süreci

KIDO veri setinin tam olarak nereden geldiği, kimlerin tarafından etiketlendiği, hangi standartlara göre Happiness/Sadness ve Anger/Fear/Happiness/Sadness sınıflarına ayrıldığı commit geçmişinden kesin olarak belirlenemiyor.

**Bu bilgi tez için kritiktir ve mutlaka belgelenmelidir.**

## 7. Klinik Geçerlilik

Sistemin bir klinisyen veya psikoloji uzmanı tarafından değerlendirilip değerlendirilmediği commit geçmişinde görünmemektedir.

## 8. Yeni 4-Sınıflı Modelin Performansı

`eval_test.py` yazılmış olmakla birlikte, yeni 4-sınıflı sistemin değerlendirme sonuçları repo'da mevcut değildir. Bu, model eğitiminin henüz tamamlanmadığını veya sonuçların commit'lenmediğini göstermektedir.

## 9. Consensus ve Highconf Pipeline'larının Fiili Eğitim Başarısı

`out/` klasöründe pipeline çıktıları mevcuttur; ancak bu pseudo-etiketli verilerle eğitilen öğrenci modelinin test performansı belgelenmemiştir.

---

# Tahmine Dayalı Yorumlar

Bu belgede yapılan yorumlar arasında şunlar kesin kanıta dayanmamaktadır:

| Yorum | Kanıt Düzeyi |
|---|---|
| "Metin verisi Türkçe metinlerden oluşuyordu" | Zayıf (dbmdz/bert-base-turkish-cased seçiminden çıkarım) |
| "Tkinter'dan React'e geçiş performans sorunlarından değil mimari tercihten" | Tahmini |
| "Sessiz dönemde yerel geliştirme yapıldı" | Tahmini |
| "Çok modlu yaklaşım performans sorunundan terk edildi" | Tahmini — gerçek neden bilinmiyor |
| "KIDO veri setinde dengesiz sınıf dağılımı var" | Orta (cinsiyet sınıfı için görülen, duygu için test setinde dengeli) |
| "label_with_model_v2.py, v1'deki hataları düzeltiyor" | Tahmini (isimlendirmeden) |

---

# Tez Yazarken Dikkat Edilmesi Gerekenler

### 1. "Çok modlu modelin başarısız olduğu" yazılmamalı
Bu kesin olarak belgelenmiş değildir. Doğru ifade: "çok modlu yaklaşımdan yalnızca görüntü tabanlı mimariye geçiş yapılmıştır."

### 2. %94 doğruluk oranı dikkatli kullanılmalı
Bu sonuç yalnızca 5 epoch eğitim ve dondurulmuş BERT ile elde edilmiştir. Tam fine-tuning veya daha uzun eğitim farklı sonuçlar verebilirdi. Ayrıca bu sonuç 2-sınıflı dengeli duygu görevine aittir; 4-sınıflı görev için analogy kurmak yanıltıcı olabilir.

### 3. Pseudo-etiket sayısı veri sayısı olarak sunulmamalı
~23.000 "pseudo-etiketli örnek" gerçek anlamda etiketlenmiş örnek değildir. "Model tarafından etiketlenmiş" veya "pseudo-etiketlenmiş" olarak net biçimde tanımlanmalıdır.

### 4. Klinik doğrulama olmadığını belirtmek şart
Sistem bir klinisyen tarafından doğrulanmamıştır. "Klinik karar destek sistemi" değil, "araştırma prototipi" olarak tanımlanmalıdır.

### 5. Cinsiyet sınıflandırması artık hedef değil
Yeni 4-sınıflı sistemde cinsiyet sınıflandırması yer almamaktadır. Tezde bu değişiklik açıkça belirtilmelidir.

---

# Öğrencinin Sonradan Ekleyebileceği Bilgiler

Aşağıdaki bilgiler tez yazarı tarafından eklenmelidir çünkü bunlar commit geçmişinden çıkarılamaz:

- [ ] Projenin tam tez başlığı ve araştırma sorusu
- [ ] KIDO veri setinin kaynağı ve etiket üretim süreci
- [ ] Multimodal modelden vazgeçilmesinin gerçek nedeni
- [ ] Tez danışmanının yönlendirmeleri ve aldığı kararlar
- [ ] Sessiz dönemlerde yapılan çalışmalar (literatür tarama, klinik görüşmeler vb.)
- [ ] Grad-CAM görsellerinin klinik anlamı (bir uzmanla tartışıldıysa)
- [ ] Yeni 4-sınıflı modelin eğitim ve test sonuçları
- [ ] Kullanıcı testi veya klinik değerlendirme sonuçları (varsa)
- [ ] Çalışmanın etik kurul onayı durumu (çocuk verisi söz konusu olduğundan önemli)
- [ ] HuggingFace ve Roboflow veri setlerinin lisans durumu

---

# Commit Mesajı Kalitesi Hakkında Not

Projedeki commit mesajları iki farklı kalite seviyesindedir:

**İyi mesajlar** (genellikle `feat:` veya `chore:` önekli):
- `feat: initialize React project with Vite, Tailwind CSS, and TypeScript`
- `feat: add desktop application with embedded FastAPI server`
- `chore: remove legacy dataset and reset old AI stack`

**Yetersiz mesajlar** (analizi zorlaştıran):
- `Ağırlık düzenleme` — neyin değiştiği tam anlaşılmıyor
- `Ezber cümleler ve GUI eklendi` — teknik ayrıntı eksik
- `Save: push all local changes` — hiçbir bilgi vermiyor
- `Auto-commit: save changes before push (assistant)` — otomatik oluşturulmuş

Yetersiz commit mesajlı değişikliklerin analizi, diff içeriğine dayandırılmıştır; bu nedenle bu bölümlerdeki yorumlar tahmine dayalıdır.
