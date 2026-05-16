# 11 — Zaman Çizelgesi

Bu dosya, commit tarihlerine dayalı proje zaman çizelgesini sunmaktadır. Yalnızca repository'de commit bulunan tarihler ve olaylar yer almaktadır. Commit'e yansımayan faaliyetler bu dosyada yer almaz.

---

# Zaman Çizelgesi

| Tarih | Geliştirme Aşaması | İlgili Commitler | Açıklama |
|---|---|---|---|
| 2025-11-30 | **Proje Kuruluşu + İlk Model** | `ec7d0f8` | İlk commit: KIDO veri seti, eğitim scripti, .gitignore |
| 2025-11-30 | **Multimodal Model Mimarisi** | `b8b32b2` | EfficientNet-B0 + Türkçe BERT modeli, freeze parametreleri |
| 2025-11-30 | **GUI + Açıklanabilirlik** | `d494e7b` | Tkinter GUI, Grad-CAM, kural tabanlı açıklayıcı |
| *2025-12-01 — 2026-02-21* | **Commit Yok** | — | Bu tarih aralığında repository'de commit yoktur |
| 2026-02-22 | **GUI İyileştirme** | `339a738` | Kaydırılabilir metin alanı, açıklama yeniden düzenleme |
| 2026-02-22 | **React Projesi Kurulumu** | `a04e560` | Vite + TypeScript + Tailwind CSS |
| 2026-02-22 | **Çok Dil Desteği** | `3b481f8` | i18n (Türkçe/İngilizce) |
| 2026-02-22 | **FastAPI Backend** | `08e1303` | REST API, analiz sayfası, CORS |
| 2026-02-22 | **Açıklama API Entegrasyonu** | `1476c63` | API yanıtına explanation alanı eklendi |
| 2026-02-22 | **Etiket Yerelleştirmesi** | `ef0af36` | Duygu/cinsiyet etiketleri dil bazlı |
| 2026-02-22 | **Raporlama Altyapısı** | `bab2958` | run_report.py, confusion matrix — **Duygu F1=0.9435** |
| 2026-03-12 | **DOCX Rapor Üretici** | `16fa3d3` | Markdown → DOCX dönüştürücü, tez şablonu |
| 2026-03-12 | **Masaüstü Uygulama** | `2a6895c` | PyInstaller, pywebview, Inno Setup |
| 2026-03-12 | **Refactoring + Grafikler** | `72d8a7b` | Kod yapısı, /about sayfası görselleri |
| *2026-03-13 — 2026-04-18* | **Commit Yok** | — | Bu tarih aralığında repository'de commit yoktur |
| 2026-04-19 | **Mimari Sıfırlama** | `5311334` | Eski AI yığını kaldırıldı, README yeniden yazıldı |
| 2026-04-20 | **Yeni Plan** | `fb8602a` | Backend V1 mikro-sprint yürütme planı |
| *2026-04-21 — 2026-05-07* | **Commit Yok** | — | Bu tarih aralığında repository'de commit yoktur |
| 2026-05-08 | **Yeni Altyapı** | `dc64027` | .env, dataset reorganizasyonu |
| 2026-05-10 | **Pseudo-Etiketleme Scriptleri** | `73ff5de` | label_with_*.py, build_manifest_*.py, pipeline scriptleri |
| 2026-05-14 | **Pipeline Çıktıları** | `a846643` | highconf (F1=0.6694) + consensus (F1=0.5721) pipeline çıktıları |

---

# Zaman Çizelgesi Görsel Özeti

```
2025-11     ████ [Proje başlangıcı: multimodal model + GUI + Grad-CAM]
2025-12     ░░░░ [Commit yok]
2026-01     ░░░░ [Commit yok]
2026-02-22  ████████ [YOĞUN SPRINT: React + FastAPI + i18n + Raporlama — Duygu F1=0.9435]
2026-03-12  ████ [Masaüstü paketleme + DOCX + Refactoring]
2026-03-13  ░░░░ [Commit yok]
2026-04-19  ██ [SIFIRLAMA: Legacy AI kaldırıldı]
2026-04-20  █  [Yeni plan dokümantasyonu]
2026-04-21  ░░░░ [Commit yok]
2026-05-08  █  [Ortam yapılandırması]
2026-05-10  ██ [Pseudo-etiketleme altyapısı]
2026-05-14  █  [Pipeline çıktıları — highconf F1=0.6694, consensus F1=0.5721]
```

---

# Geliştirme Yoğunluğu Analizi

| Dönem | Commit Sayısı | Durum |
|---|---|---|
| Kasım 2025 | 3 | Aktif |
| Aralık 2025 – 21 Şubat 2026 | 0 | **Commit yok** |
| 22 Şubat 2026 | 7 | **En yoğun gün** |
| 12 Mart 2026 | 3 | Aktif |
| 13 Mart – 18 Nisan 2026 | 0 | **Commit yok** |
| 19–20 Nisan 2026 | 2 | Aktif |
| 21 Nisan – 7 Mayıs 2026 | 0 | **Commit yok** |
| 8–14 Mayıs 2026 | 3 | Aktif |

---

# Önemli Tarih Notları

1. **22 Şubat 2026 — En Yoğun Gün:** Tek günde React projesi, i18n, FastAPI, açıklama API'si ve raporlama altyapısı oluşturuldu. 7 commit. Bu tarihte `bab2958` commiti ile ölçülen değerler: Duygu Accuracy=%94.36, F1=0.9435, ROC-AUC=0.9866.

2. **19 Nisan 2026 — Mimari Sıfırlama:** Eski çok modlu sistem `5311334` commiti ile kaldırıldı. Bu kararın teknik gerekçesini doğrulayan log veya metrik repository'de bulunmamaktadır.

3. **Commit Olmayan Dönemler:** Üç ayrı dönemde (Aralık 2025 – Şubat 2026, Mart – Nisan 2026, Nisan – Mayıs 2026) repository'de commit yoktur. Bu dönemlerde neler yapıldığı commit geçmişinden belirlenememektedir.

---

# Commit Bazlı Aktif Geliştirme Süresi

| Aşama | Süre (commit tarihlerine göre) |
|---|---|
| İlk prototip + GUI | 1 gün (30 Kasım 2025) |
| Web + API geliştirme | 1 gün (22 Şubat 2026) |
| Masaüstü + Raporlama | 1 gün (12 Mart 2026) |
| Karar ve sıfırlama | 2 gün (19–20 Nisan 2026) |
| Yeni sistem geliştirme | 3 gün (8–14 Mayıs 2026) |
| **Commit bulunan toplam gün sayısı** | **8 gün** |
| **Toplam takvim süresi** | **~6 ay (30 Kasım 2025 – 14 Mayıs 2026)** |

**Not:** Aktif geliştirme süresi commit sayısına göre değil, commit tarihlerine göre hesaplanmıştır. Bu tablo yalnızca repository'ye yansıyan faaliyetleri kapsamaktadır.
