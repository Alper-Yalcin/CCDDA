# 10 — Tezde Kullanılabilecek Geliştirme Süreci Anlatımı

Bu dosya, doğrudan teze aktarılabilecek akademik düzeyde paragraflar içermektedir. Tüm ifadeler, commit geçmişi ve kod incelemesinden elde edilen kanıtlara dayanmaktadır. Belirsiz noktalarda "muhtemelen", "anlaşıldığı kadarıyla" gibi ifadeler kullanılmıştır.

> **Uyarı:** Bu paragraflar tez yazımı için başlangıç noktası niteliğindedir. Tez yazarı, kendi deneyimlediği ancak commit'lere yansımayan bilgileri eklemeli ve sonuçları kesinleştirmelidir.

---

# Tezde Kullanılabilecek Geliştirme Süreci Anlatımı

## Projenin Başlangıcı

Bu çalışma, çocukların el çizmesi resimlerinden duygusal durumun otomatik olarak tespit edilmesini amaçlamaktadır. Araştırmanın motivasyonu, klinik psikoloji pratiğinde yaygın kullanılan projektif çizim testlerinin değerlendirilme sürecindeki öznellik ve uzman bağımlılığıdır. Yapay zeka destekli bir analiz aracının, klinisyenlere nesnelleştirilmiş ve tekrar üretilebilir bir referans sunabileceği hipotezi temel alınmıştır.

Projenin veri tabanını KIDO (Kido — kesin açılım commit geçmişinde belirtilmemiştir) veri seti oluşturmaktadır. Bu veri seti, Türk okul çocuklarına ait el çizmesi resimler içermekte olup dosya adlandırma şemasından (`[okul_id]-[sınıf]-[öğrenci_id]-[cinsiyet]-[duygu].jpg`) her çizime ait okul, sınıf, öğrenci, cinsiyet ve duygu etiketleri çıkarılabilmektedir. Başlangıçta 10.856 etiketli örnek kullanılmıştır.

---

## İlk Prototipin Oluşturulması

Proje, Kasım 2025 sonunda çok modlu (multimodal) bir derin öğrenme sistemi olarak hayata geçirilmiştir. Bu ilk mimaride iki modalite bir araya getirilmiştir: görüntü verisi EfficientNet-B0 ağıyla, metin verisi ise Türkçe BERT modeli (`dbmdz/bert-base-turkish-cased`) aracılığıyla kodlanmıştır. Her iki modaliteden elde edilen özellik vektörleri projeksiyon katmanlarıyla ortak bir 1024 boyutlu uzaya dönüştürülmüş ve birleştirilerek çok görevli bir sınıflandırıcıya aktarılmıştır. Sistem, duygu sınıflandırması (Mutluluk / Üzüntü) ve cinsiyet sınıflandırması (Kız / Erkek) olmak üzere iki bağımsız görevi eş zamanlı gerçekleştirmiştir.

Eğitim sürecinde BERT parametreleri dondurulmuş (`freeze_bert=True`), EfficientNet-B0 ise ince ayara tabi tutulmuştur. Bu asimetrik dondurma stratejisi, 116 milyon toplam parametreli modelde eğitilebilir parametre sayısını 5.6 milyona indirmiş; böylece sınırlı veri kümesinde aşırı öğrenme riski azaltılmıştır.

---

## Açıklanabilirlik Katmanının Geliştirilmesi

Klinik ortamlarda yapay zeka sistemlerinin kabul görmesi, yalnızca yüksek doğruluk oranıyla değil, aynı zamanda yorumlanabilirlikle de ilgilidir. Bu gerçeklikten hareketle, sisteme Grad-CAM (Gradient-weighted Class Activation Mapping) görselleştirme modülü entegre edilmiştir. Grad-CAM, modelin sınıflandırma kararını verirken çizimin hangi bölgelerine odaklandığını ısı haritası olarak görselleştirmektedir. Duygu ve cinsiyet sınıflandırması için ayrı ısı haritaları üretilmektedir.

Buna ek olarak, kural tabanlı bir açıklama üreticisi geliştirilmiştir. Bu modül, model tahminini ve güven skorunu girdi olarak alarak önceden tanımlanmış şablonlar aracılığıyla doğal dil açıklamaları üretmektedir. Sistemin mevcut sürümü, büyük dil modeli (LLM) tabanlı dinamik açıklama üretimini de desteklemektedir; ancak bu özellik isteğe bağlı bir API anahtarı gerektirmektedir.

---

## Arayüz Geliştirme Süreci

Sistemin kullanılabilirliğini artırmak amacıyla iki aşamalı bir arayüz geliştirme süreci izlenmiştir.

**İlk Prototip (Kasım 2025):** Tkinter kütüphanesi ile yerel masaüstü arayüzü geliştirilmiştir. Bu arayüz, görüntü yükleme, model çalıştırma ve Grad-CAM görselleştirmesi ile açıklama metni sunumu işlevlerini içermektedir. Kullanıcı geri bildirimleri doğrultusunda, uzun açıklama metinlerinin okunabilmesi için kaydırılabilir metin alanı eklenmiştir.

**Web Tabanlı Sistem (Şubat 2026):** Daha geniş erişilebilirlik ve modern kullanıcı deneyimi sağlamak amacıyla React ve TypeScript tabanlı web uygulamasına geçilmiştir. Vite derleme aracı ve Tailwind CSS ile oluşturulan arayüz, Türkçe ve İngilizce olmak üzere iki dil seçeneği sunmaktadır. Arka uç FastAPI ile yeniden yapılandırılmış; görüntü yükleme, model çıkarımı ve açıklama üretimini tek bir REST API endpoint'inde birleştiren `/predict` servisi oluşturulmuştur.

**Masaüstü Paketleme (Mart 2026):** İnternet bağlantısı gerektirmeyen klinik ortamlar için PyInstaller kullanılarak bağımsız Windows yürütülebilir paketi oluşturulmuştur. Bu paket, FastAPI sunucusunu ve React arayüzünü bir arada barındırmakta; pywebview aracılığıyla yerel tarayıcı penceresi açmaktadır.

---

## Mimari Yeniden Yapılanma

Nisan 2026'da projenin temel yönü değiştirilmiştir. Çok modlu yaklaşımın araştırma sorusuyla olan uyumu yeniden değerlendirilmiş; BERT tabanlı metin kodlayıcısı ve ilgili tüm bileşenler devre dışı bırakılmıştır. Bu kararın temel gerekçesi commit geçmişinde açıkça belirtilmemiş olmakla birlikte, README içeriğinde "eski multimodal AI hattının bilinçli olarak kaldırıldığı" ve "yeni etiketli görüntü-only veriyle sıfırdan kurulacak yeni AI sistemi için hazırlık yapıldığı" ifade edilmektedir.

Aynı dönemde, sınıflandırma hedefi de iki sınıftan (Mutluluk/Üzüntü) dört sınıfa (Öfke, Korku, Mutluluk, Üzüntü) genişletilmiştir. Bu genişleme, klinik psikoloji literatüründeki temel duygu taksonomileriyle daha iyi örtüşmektedir.

---

## Veri Büyütme: Yarı Denetimli Öğrenme

Derin öğrenme modellerinin yüksek başarı oranı göstermesi için büyük miktarda etiketli veri gerekmektedir. Çocuk çizimleri gibi özel bir alana ait veri kümelerinin manuel etiketlenmesi hem zaman alıcı hem de uzman gerektiren bir süreçtir. Bu kısıtı aşmak amacıyla Mayıs 2026'dan itibaren yarı denetimli öğrenme (semi-supervised learning) paradigması benimsenmiştir.

Uygulanan yaklaşım iki tamamlayıcı stratejiden oluşmaktadır:

**Yüksek Güvenilirlikli Pseudo-Etiketleme:** Önceden eğitilmiş bir öğretmen model (EfficientNet-B3), etiketsiz görüntüler üzerinde çıkarım yapmaktadır. Modelin tahmin güveni belirli bir eşiği (0.75 veya 0.85) aşan örnekler, yeni eğitim verisi olarak kabul edilmektedir. Bu yaklaşım yaklaşık 19.000 ila 23.000 ek örnek üretmiştir.

**Uzlaşma Tabanlı Etiketleme:** Birden fazla bağımsız modelin (HuggingFace modelleri, Ollama yerel model, mevcut öğretmen model) aynı görüntü için aynı etiketi üretmesi şartı aranmaktadır. Üç modelin tam mutabakatı (~8.300 örnek) ile elde edilen bu küme, tek model etiketlemesine kıyasla daha güvenilir kabul edilmektedir.

Ek olarak, HuggingFace'ten elde edilen çizim veri kümesi ve Roboflow Drawing Facial Emotions veri seti dahil edilerek kaynak çeşitlendirmesi yapılmıştır.

---

## Sistem Mimarisi

Sistemin güncel hedef mimarisi şu katmanlardan oluşmaktadır:

1. **Veri Katmanı:** KIDO veri seti + harici çizim veri kümeleri + pseudo-etiketlenmiş veriler
2. **Model Katmanı:** EfficientNet-B3 tabanlı 4-sınıflı görüntü sınıflandırıcısı (`ClinicalFusionClassifier`)
3. **API Katmanı:** FastAPI REST endpoint'i (`/predict`)
4. **Arayüz Katmanı:** React web uygulaması (Türkçe/İngilizce)
5. **Açıklanabilirlik Katmanı:** Grad-CAM görselleştirme + LLM/kural tabanlı açıklama

---

## Elde Edilen Sonuçlar

Daha önceki çok modlu sistem üzerinde gerçekleştirilen değerlendirme, duygu sınıflandırması görevinde %94.36 doğruluk oranı ve 0.9866 ROC-AUC değeri ortaya koymuştur. Cinsiyet sınıflandırmasında bu değerler sırasıyla %77.12 ve 0.8542 olarak elde edilmiştir. Duygu görevindeki yüksek performans, el çizmesi resimlerin duygu sinyali taşıdığını ve makine öğrenimi yöntemleriyle bu sinyalin ayırt edilebildiğini göstermektedir.

Yeni 4-sınıflı sistemin değerlendirme sonuçları, model eğitimi henüz tamamlanmadığından bu belgede mevcut değildir.

---

## Etik Değerlendirme

Sistemin klinik tanı aracı olarak sunulması amaçlanmamaktadır. Değerlendirme raporu (`artifacts/report_run/REPORT.md`) bu konuda açık bir uyarı içermektedir: "Bu sistem klinik tanı aracı değildir. Çıktılar yalnızca araştırma ve karar-destek amaçlı değerlendirilmelidir; nihai yorum uzman profesyoneller tarafından yapılmalıdır."

Yapay zeka destekli sistemlerin klinik ortamlarda yalnızca klinisyenin değerlendirmesini desteklemek amacıyla kullanılması, hem tıp etiği hem de teknik açıdan doğru yaklaşımdır.

---

## Sonuç

Bu proje, çocuk çizimi tabanlı duygu analizi alanında makine öğrenimi yöntemlerinin uygulanabilirliğini araştırmakta; yüksek doğruluk oranı elde eden, açıklanabilirlik mekanizmalarıyla donatılmış ve klinik ortamlarda kullanılabilecek bir prototip sistem sunmaktadır. Geliştirme süreci, çok modlu mimariden sade görüntü tabanlı mimariye, ikili sınıflandırmadan 4-sınıflı taksonomiye ve sınırlı etiketli veriden yarı denetimli öğrenmeye doğru gerçekleşen iteratif bir evrimi yansıtmaktadır.
