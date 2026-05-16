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
