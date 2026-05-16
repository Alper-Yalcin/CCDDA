# 01 — Commit Kronolojisi

Bu dosya, projenin tüm commit geçmişini en eski committen en yeniye doğru, teknik analiz ve tez bağlamında yorumlarıyla listeler.

---

## Commit Tablosu

| # | Commit ID | Tarih | Commit Mesajı | Kategori | Değişen Dosyalar (Özet) | Teknik Yorum |
|---|---|---|---|---|---|---|
| 1 | `ec7d0f8` | 2025-11-30 | first commit | `setup` | `.gitignore`, `Dataset/Images/Education/test/Primary/` (çok sayıda resim), `src/train/train_multimodal.py`, diğer src dosyaları | Projenin başlangıç anı. Hem veri seti hem de eğitim kodu aynı committe. KIDO veri seti görüntüleri ve çok modlu EfficientNet+BERT eğitim scripti birlikte eklendi. |
| 2 | `b8b32b2` | 2025-11-30 | Ağırlık düzenleme | `feature` | `src/models/multimodal_effnet_bert.py`, `src/train/train_multimodal.py` | Model mimarisi tanımlandı. EfficientNet-B0 görüntü kodlayıcı + Türkçe BERT metin kodlayıcı birleştirilerek iki kafadan (emotion head, gender head) oluşan çok görevli model oluşturuldu. "Ağırlık düzenleme" ifadesi muhtemelen freeze/unfreeze parametrelerinin düzenlenmesine atıfta bulunmaktadır. |
| 3 | `d494e7b` | 2025-11-30 | Ezber cümleler ve GUI eklendi | `feature` + `ui` | `src/app/gui_multimodal.py`, `src/app/tk_app.py`, `src/data/dataset.py`, `src/explain/gradcam.py`, `src/explain/perception_api.py`, `src/explain/predict_and_explain.py`, `src/explain/rule_based_explainer.py`, `src/explain/text_explain.py`, Grad-CAM görsel çıktıları | Büyük commit. Tkinter GUI eklendi; Grad-CAM açıklanabilirlik modülü, kural tabanlı açıklayıcı ve metin tabanlı açıklayıcı (olasılıkla "ezber cümleler" ifadesiyle kastedilen) eklendi. Grad-CAM görsel çıktıları da commite dahil edilmiş. |
| 4 | `339a738` | 2026-02-22 | Add scrollable text widget for explanation and refactor explanation generation | `ui` + `refactor` | `src/app/gui_multimodal.py`, `src/app/tk_app.py` | ~3 aylık boşluktan sonra ilk commit. Tkinter GUI'de açıklama metni için kaydırılabilir metin alanı eklendi; açıklama üretimi yeniden düzenlendi. Ara dönemde commitlenmemiş çalışmalar yapılmış olabilir. |
| 5 | `a04e560` | 2026-02-22 | feat: initialize React project with Vite, Tailwind CSS, and TypeScript | `setup` | `Web/` dizininin tamamı (React projesi iskelet) | Önemli mimari karar: Tkinter GUI'den web tabanlı arayüze geçiş. React + Vite + TypeScript + Tailwind CSS projesinin ilk kurulumu yapıldı. |
| 6 | `3b481f8` | 2026-02-22 | feat: implement internationalization support with language selection | `feature` | `Web/src/` (i18n entegrasyonu) | Aynı gün React projesine hemen ardından çoklu dil desteği (Türkçe/İngilizce) eklendi. i18next kütüphanesi kullanıldığı dosya içeriğinden anlaşılmaktadır. |
| 7 | `08e1303` | 2026-02-22 | feat: enhance analysis page with text input and error handling; add FastAPI backend for predictions | `feature` + `api` | `Web/src/App.tsx`, `Web/src/locales/*.json`, `Web/vite.config.ts`, `api_server.py` (yeni), `requirements.txt` | İlk FastAPI arka ucunun oluşturulduğu commit. `api_server.py` 131 satırla eklendi; React analiz sayfasına metin girişi ve hata yönetimi eklendi. Vite proxy yapılandırması da güncellendi. |
| 8 | `1476c63` | 2026-02-22 | feat: add explanation field to API result and update UI to display model explanations | `feature` | `Web/src/App.tsx`, `api_server.py` | API yanıtına açıklama alanı eklendi; UI bu alanı gösterecek şekilde güncellendi. Model çıktılarının sadece sınıf değil, açıklama metni de döndürmesi sağlandı. |
| 9 | `ef0af36` | 2026-02-22 | feat: add localization support for emotion and gender labels; update explanation generation in API | `feature` | `Web/src/App.tsx`, `api_server.py` | Duygu ve cinsiyet etiketleri için yerelleştirme desteği eklendi. API açıklama üretimi güncellendi. 189 satır ekleme ile büyük bir güncelleme. |
| 10 | `bab2958` | 2026-02-22 | Add report runner script and configuration for quick testing | `test` + `docs` | `artifacts/report_run/REPORT.md`, `artifacts/report_run/figures/` (confusion matrix, ROC curve), `run_report.py`, `run_args.json` | Model değerlendirme ve raporlama altyapısı eklendi. Eğitim, değerlendirme ve rapor üretme sürecini otomatize eden script yazıldı. Confusion matrix ve ROC eğrisi görselleştirmeleri üretildi ve kaydedildi. |
| 11 | `16fa3d3` | 2026-03-12 | Add script to generate DOCX reports from Markdown using a template | `feature` | `build_report_docx.py`, `Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx`, `artifacts/docx_inspect/` | Markdown'dan DOCX formatına dönüşüm scripti oluşturuldu. Referans DOCX şablonu ile stili koruyan dönüşüm yapılıyor. Tez belgesi şablonu (`Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx`) da bu committe eklendi. |
| 12 | `2a6895c` | 2026-03-12 | feat: add desktop application with embedded FastAPI server and React frontend | `feature` | `desktop_app.py`, `desktop_app.spec`, `src/app_paths.py`, `Web/src/App.tsx` (+346 satır), `api_server.py` (büyük güncelleme), `requirements-desktop.txt`, Inno Setup scripti, `build_desktop.ps1` | Büyük özellik: FastAPI + React'i saran masaüstü uygulaması oluşturuldu. PyInstaller ile paketleme yapılandırması, pywebview ile tarayıcı penceresi açma, Windows kurulum paketi oluşturma altyapısı kuruldu. |
| 13 | `72d8a7b` | 2026-03-12 | Refactor code structure for improved readability and maintainability | `refactor` | `desktop_app.py` (13 satır), `.gitignore`, `Web/public/about/` (grafik görseller) | Kod yapısı ve okunabilirlik düzenlemesi. Performans grafikleri (confusion matrix, ROC, eğitim eğrileri, örnek tahminler) web uygulamasının `/about` sayfasına eklendi. |
| 14 | `5311334` | 2026-04-19 | chore: remove legacy dataset and reset old AI stack | `cleanup` | `Dataset/Images/Education/` (çok sayıda resim silindi) ve eski AI modülleri | **Kritik mimari sıfırlama.** Eski çok modlu AI yığını (BERT dahil) bilinçli olarak kaldırıldı. Eski eğitim veri seti silindi. README, yeni yönü açıklayacak şekilde güncellendi. |
| 15 | `fb8602a` | 2026-04-20 | feat: add comprehensive execution plan for Backend V1 micro-sprints | `docs` | Plan/döküman dosyaları | Backend V1 için mikro-sprint yürütme planı eklendi. Yeni AI altyapısının nasıl inşa edileceğini belgeleyen tasarım dokümanı niteliğinde. |
| 16 | `dc64027` | 2026-05-08 | Auto-commit: save changes before push (assistant) | `setup` + `feature` | `.env`, `.env.example`, `Dataset/Images/Education/` (bazı resimler), `.claude/scheduled_tasks.lock` | Ortam değişkeni dosyaları ve Claude Code asistan yapılandırması eklendi. "Auto-commit" ifadesinden bu commitin araç tarafından otomatik oluşturulduğu anlaşılmaktadır. |
| 17 | `73ff5de` | 2026-05-10 | Save: push all local changes | `feature` + `cleanup` | `Dataset/Images/Emotion_4Class/` (büyük veri seti değişiklikleri), çeşitli pipeline scriptleri | Yeni 4-sınıflı veri seti yapılandırması. Pseudo-etiketleme scriptleri (`label_with_hf.py`, `label_with_ollama.py`, `build_manifest_*.py` vb.) eklendi/güncellendi. "Save" mesajı anlamlı değil; diff içeriği çok daha kapsamlı değişiklikler içeriyor. |
| 18 | `a846643` | 2026-05-14 | chore: add new phenotype pipelines and output files | `feature` | `out/consensus_pipeline/`, `out/highconf_pipeline/` (büyük CSV ve JSON çıktıları) | Pseudo-etiketleme pipeline çıktıları: consensus (3 model mutabakatı) ve high-confidence (güven eşiği) manifests üretildi. Çıktı dosyaları doğrudan repo'ya eklendi. |

---

## Commit Kategori Dağılımı

| Kategori | Commit Sayısı | Commitler |
|---|---|---|
| `setup` | 2 | ec7d0f8, a04e560 |
| `feature` | 9 | b8b32b2, d494e7b, 08e1303, 1476c63, ef0af36, 2a6895c, dc64027, 73ff5de, a846643 |
| `ui` | 2 | 339a738, a04e560 |
| `refactor` | 2 | 339a738, 72d8a7b |
| `api` | 1 | 08e1303 |
| `test` | 1 | bab2958 |
| `docs` | 2 | bab2958, fb8602a |
| `cleanup` | 2 | 5311334, 73ff5de |

---

## Önemli Gözlemler

1. **İlk commit büyük**: Hem veri seti hem kod aynı anda eklendi — muhtemelen yerel geliştirme tamamlandıktan sonra ilk defa GitHub'a yüklendi.
2. **3 aylık boşluk**: Commit 3 (d494e7b, 30 Kasım 2025) ile Commit 4 (339a738, 22 Şubat 2026) arasında yaklaşık 3 ay geçmiştir. Bu dönemde yerel çalışmalar yapılmış olabilir ama commitlenmemiştir.
3. **22 Şubat 2026 yoğunluğu**: Tek günde 7 commit (4-10 arası) yapılmıştır. Büyük bir web geliştirme sprinti.
4. **Mimari sıfırlama**: Commit 14 (5311334, 19 Nisan 2026) projenin en kritik dönüm noktasıdır.
5. **Son commitler anlamsız mesajlar içeriyor**: "Save", "Auto-commit" gibi mesajlar — diff içeriğinden analiz edildi.
