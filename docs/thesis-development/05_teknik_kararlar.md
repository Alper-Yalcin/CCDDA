# 05 — Teknik Kararlar

Bu dosya, projede alınan önemli teknik kararları belgeler. Her karar için kanıt, olası gerekçe ve avantaj/dezavantajlar sunulmuştur.

---

## Teknik Karar 1: EfficientNet-B0 Görüntü Kodlayıcı Seçimi

### Karar
Görüntü özellik çıkarımı için EfficientNet-B0 (ImageNet ön eğitimli) kullanıldı.

### Kanıt
`src/models/multimodal_effnet_bert.py` (`b8b32b2`): `from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights`
`run_highconf_pipeline.py`: Daha sonra B2 ve B3 varyantları da eklendi.

### Olası Gerekçe
EfficientNet ailesi, parametre sayısı-doğruluk dengesi açısından benchmark değerlendirmelerinde üstün performans göstermektedir. B0, serinin en hafif modelidir ve görece sınırlı GPU kaynaklarında bile çalışabilir. Transfer öğrenimi ile ImageNet ağırlıkları aktarılarak küçük veri setlerinde bile iyi başlangıç noktası elde edilmiştir.

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

### Olası Gerekçe
Veri kümesi Türk okul çocuklarına aittir ve olasılıkla metin verisi de Türkçedir. Türkçe'ye özgü BERT modeli, dil özelliklerini (eklemeli yapı, morfoji) daha iyi temsil etmektedir. `dbmdz/bert-base-turkish-cased` HuggingFace üzerinde yaygın kullanılan ve iyi belgelenmiş bir Türkçe BERT modelidir.

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

### Olası Gerekçe
Bu asimetrik dondurma stratejisi standart bir transfer öğrenimi tekniğidir. BERT'in 110M+ parametresi küçük veri setlerinde aşırı öğrenmeye (overfitting) yol açabilir; dondurma bunu önler. EfficientNet'in görüntüye özgü alt katmanlarının ince ayara (fine-tuning) ihtiyacı daha büyüktür.

### Avantajları
- Eğitim hızlanır (BERT gradyanları hesaplanmaz)
- Küçük veri setlerinde aşırı öğrenme riski azalır
- Eğitilebilir parametre sayısı: 116.2M toplam → yalnızca 5.6M eğitilebilir

### Dezavantajları / Sınırlamaları
- Frozen BERT, alana özgü metin bilgisini öğrenemez
- Metin ve görüntü özelliklerinin entegrasyonu daha zayıf olabilir

### Tezde Kullanılabilecek Anlatım
Eğitim kararlılığını sağlamak ve aşırı öğrenmeyi önlemek amacıyla BERT parametreleri dondurulmuş, yalnızca projeksiyon katmanları ve görüntü kodlayıcısı eğitime dahil edilmiştir. Bu strateji, 116 milyon parametreli modelde eğitilebilir parametre sayısını 5.6 milyona indirmiştir.

---

## Teknik Karar 4: FastAPI + React Mimarisi

### Karar
Backend için FastAPI, frontend için React + Vite seçildi.

### Kanıt
`08e1303` commitinde `api_server.py` (FastAPI) ve `Web/` (React) eş zamanlı eklendi.

### Olası Gerekçe
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

### Olası Gerekçe
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

### Olası Gerekçe
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

### Olası Gerekçe
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

### Olası Gerekçe
Klinik ortamlarda internet bağlantısı kısıtlı olabilir ya da kurulum yapma yetkisi bulunmayabilir. Bağımsız `.exe` formatı bu engeli ortadan kaldırır. PyInstaller, Python bağımlılıklarını tek bir pakette toplar.

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
