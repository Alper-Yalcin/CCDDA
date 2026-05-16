# 01 — Commit Kronolojisi

Bu dosya, projenin tüm commit geçmişini en eski committen en yeniye doğru, diff analizi ve tez bağlamıyla listeler. Commit mesajlarından çıkarılamayan teknik detaylar diff içeriğine dayandırılmıştır. Kanıt bulunmayan yorumlar için bu durum açıkça belirtilmiştir.

---

## Commit Tablosu

| # | Commit ID | Tarih | Commit Mesajı | Kategori | Değişen Dosyalar (Özet) | Teknik Analiz |
|---|---|---|---|---|---|---|
| 1 | `ec7d0f8` | 2025-11-30 | first commit | `setup` | `.gitignore`, `Dataset/Images/Education/test/Primary/` (çok sayıda resim), `src/train/train_multimodal.py`, diğer src dosyaları | Projenin başlangıç commiti. KIDO veri seti görüntüleri ve çok modlu EfficientNet+BERT eğitim scripti aynı anda repo'ya eklendi. |
| 2 | `b8b32b2` | 2025-11-30 | Ağırlık düzenleme | `feature` | `src/models/multimodal_effnet_bert.py`, `src/train/train_multimodal.py` | Commit diff: `multimodal_effnet_bert.py` dosyasına EfficientNet-B0 + Türkçe BERT birleşik mimari eklendi. `train_multimodal.py`'de `--freeze_bert=True`, `--freeze_effnet=False` parametreleri tanımlandı. "Ağırlık düzenleme" mesajı bu parametre değişikliğini ifade etmektedir. |
| 3 | `d494e7b` | 2025-11-30 | Ezber cümleler ve GUI eklendi | `feature` + `ui` | `src/app/gui_multimodal.py`, `src/app/tk_app.py`, `src/data/dataset.py`, `src/explain/gradcam.py`, `src/explain/perception_api.py`, `src/explain/predict_and_explain.py`, `src/explain/rule_based_explainer.py`, `src/explain/text_explain.py`, Grad-CAM görsel çıktıları | Commit mesajındaki "ezber cümleler" ifadesi `rule_based_explainer.py` içindeki önceden tanımlı şablon açıklamalara karşılık gelmektedir. Aynı committe Tkinter GUI (`gui_multimodal.py`), Grad-CAM modülü ve metin açıklayıcı eklendi. Grad-CAM görsel çıktıları da commite dahil edildi. |
| 4 | `339a738` | 2026-02-22 | Add scrollable text widget for explanation and refactor explanation generation | `ui` + `refactor` | `src/app/gui_multimodal.py`, `src/app/tk_app.py` | Commit 3 ile Commit 4 arasında yaklaşık 3 ay geçmiştir. Bu dönemde repository'de commit yoktur. Tkinter GUI'de açıklama metni için kaydırılabilir metin alanı eklendi; açıklama üretimi yeniden düzenlendi. |
| 5 | `a04e560` | 2026-02-22 | feat: initialize React project with Vite, Tailwind CSS, and TypeScript | `setup` | `Web/` dizininin tamamı (React projesi iskelet) | Tkinter GUI'den web tabanlı arayüze geçiş başladı. React + Vite + TypeScript + Tailwind CSS projesinin ilk kurulumu yapıldı. |
| 6 | `3b481f8` | 2026-02-22 | feat: implement internationalization support with language selection | `feature` | `Web/src/` (i18n entegrasyonu) | Commit diff: `i18next` kütüphanesi entegre edildi. Türkçe ve İngilizce dil dosyaları eklendi. |
| 7 | `08e1303` | 2026-02-22 | feat: enhance analysis page with text input and error handling; add FastAPI backend for predictions | `feature` + `api` | `Web/src/App.tsx`, `Web/src/locales/*.json`, `Web/vite.config.ts`, `api_server.py` (yeni, 131 satır), `requirements.txt` | `api_server.py` ilk kez oluşturuldu (131 satır). `vite.config.ts` güncellenerek React dev sunucusu FastAPI'ye proxy yapılandırıldı. |
| 8 | `1476c63` | 2026-02-22 | feat: add explanation field to API result and update UI to display model explanations | `feature` | `Web/src/App.tsx`, `api_server.py` | API yanıt formatına `explanation` alanı eklendi. UI bu alanı gösterecek şekilde güncellendi. |
| 9 | `ef0af36` | 2026-02-22 | feat: add localization support for emotion and gender labels; update explanation generation in API | `feature` | `Web/src/App.tsx`, `api_server.py` | Duygu ve cinsiyet etiketleri için dil bazlı yerelleştirme desteği eklendi. 189 satır ekleme. |
| 10 | `bab2958` | 2026-02-22 | Add report runner script and configuration for quick testing | `test` + `docs` | `artifacts/report_run/REPORT.md`, `artifacts/report_run/figures/` (confusion matrix, ROC curve), `run_report.py`, `run_args.json` | Model değerlendirme ve raporlama altyapısı eklendi. `REPORT.md` sonuçlarını içeriyor: Duygu Accuracy=%94.36, F1=0.9435, ROC-AUC=0.9866; Cinsiyet Accuracy=%77.12, F1=0.7658, ROC-AUC=0.8542. |
| 11 | `16fa3d3` | 2026-03-12 | Add script to generate DOCX reports from Markdown using a template | `feature` | `build_report_docx.py`, `Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx`, `artifacts/docx_inspect/` | Markdown'dan DOCX formatına dönüşüm scripti oluşturuldu. Tez belgesi şablonu (`Alper_YALÇIN_Cocuk_Cizimlerinden_Duygu_Analizi.docx`) repo'ya eklendi. |
| 12 | `2a6895c` | 2026-03-12 | feat: add desktop application with embedded FastAPI server and React frontend | `feature` | `desktop_app.py`, `desktop_app.spec`, `src/app_paths.py`, `Web/src/App.tsx` (+346 satır), `api_server.py` (büyük güncelleme), `requirements-desktop.txt`, Inno Setup scripti, `build_desktop.ps1` | `src/app_paths.py` dosyası `sys.frozen` kontrolü ile paketlenmiş ortamda dosya yolu çözümlemesi yapıyor. PyInstaller + pywebview ile bağımsız Windows uygulaması inşa altyapısı kuruldu. |
| 13 | `72d8a7b` | 2026-03-12 | Refactor code structure for improved readability and maintainability | `refactor` | `desktop_app.py` (13 satır), `.gitignore`, `Web/public/about/` (grafik görseller) | Kod yapısı düzenlendi. Confusion matrix, ROC eğrisi, eğitim eğrileri web uygulamasının `/about` sayfasına eklendi. |
| 14 | `5311334` | 2026-04-19 | chore: remove legacy dataset and reset old AI stack | `cleanup` | `Dataset/Images/Education/` (çok sayıda resim silindi) ve eski AI modülleri | **Kritik mimari sıfırlama.** Eski çok modlu AI yığını (BERT dahil) bilinçli olarak kaldırıldı. README güncellenerek yeni yön açıklandı. `/predict` endpoint `503` döndürecek şekilde devre dışı bırakıldı. Bu kararın teknik gerekçesini doğrulayan performans karşılaştırması veya log bulunamadı. |
| 15 | `fb8602a` | 2026-04-20 | feat: add comprehensive execution plan for Backend V1 micro-sprints | `docs` | Plan/döküman dosyaları | Backend V1 için mikro-sprint yürütme planı eklendi. |
| 16 | `dc64027` | 2026-05-08 | Auto-commit: save changes before push (assistant) | `setup` + `feature` | `.env`, `.env.example`, `Dataset/Images/Education/` (bazı resimler), `.claude/scheduled_tasks.lock` | Commit mesajındaki "Auto-commit (assistant)" ifadesi Claude Code tarafından otomatik oluşturulduğunu göstermektedir. Ortam değişkeni dosyaları eklendi. |
| 17 | `73ff5de` | 2026-05-10 | Save: push all local changes | `feature` + `cleanup` | `Dataset/Images/Emotion_4Class/` (büyük veri seti değişiklikleri), çeşitli pipeline scriptleri | Commit mesajı ("Save") anlamlı değildir; diff içeriği değişikliği açıklamaktadır. Yeni 4-sınıflı veri seti yapılandırması ve pseudo-etiketleme scriptleri eklendi. |
| 18 | `a846643` | 2026-05-14 | chore: add new phenotype pipelines and output files | `feature` | `out/consensus_pipeline/`, `out/highconf_pipeline/` (büyük CSV ve JSON çıktıları) | Pseudo-etiketleme pipeline çıktıları eklendi. Sonuçlar: Highconf 0.75 → 23.063 örnek, Macro F1=0.6694; Consensus 3/3 → 7.980 örnek, Macro F1=0.5721. |

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

1. **İlk commit büyük:** KIDO veri seti görüntüleri ve eğitim kodu aynı anda eklendi. Commit geçmişi bunu tek bir commit olarak kayıtlamıştır.
2. **3 aylık dönemde commit yok:** Commit 3 (2025-11-30) ile Commit 4 (2026-02-22) arasında repository'de commit yoktur.
3. **22 Şubat 2026 yoğunluğu:** Tek günde 7 commit (4–10 arası) yapılmıştır.
4. **Mimari sıfırlama:** Commit 14 (`5311334`, 19 Nisan 2026) eski AI yığınını kaldırmıştır. Bu kararın teknik gerekçesini doğrulayan log bulunamadı.
5. **Bilgi değeri düşük mesajlar:** "Save", "Auto-commit", "Ağırlık düzenleme" — bu commitlerde diff içeriği analiz edildi.
6. **Commit 10 somut metrik içeriyor:** `bab2958` commiti `artifacts/report_run/REPORT.md` dosyasını ekledi; içindeki metrikler kanıt kaynağı olarak kullanıldı.
