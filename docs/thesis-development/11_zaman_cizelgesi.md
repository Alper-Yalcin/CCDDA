# 11 — Zaman Çizelgesi

Bu dosya, commit tarihlerine ve içeriklerine dayalı proje zaman çizelgesini sunmaktadır.

---

# Zaman Çizelgesi

| Tarih | Geliştirme Aşaması | İlgili Commitler | Açıklama |
|---|---|---|---|
| 2025-11-30 (Gün 1) | **Proje Kuruluşu + İlk Model** | `ec7d0f8` | İlk commit: KIDO veri seti, eğitim scripti, .gitignore |
| 2025-11-30 (Gün 1) | **Multimodal Model Mimarisi** | `b8b32b2` | EfficientNet-B0 + Türkçe BERT modeli, ağırlık dondurma |
| 2025-11-30 (Gün 2) | **GUI + Açıklanabilirlik** | `d494e7b` | Tkinter GUI, Grad-CAM, kural tabanlı açıklayıcı |
| *2025-12 — 2026-01* | **Sessiz Dönem (yaklaşık 3 ay)** | — | Bu dönemde commitlenmemiş yerel çalışmalar yapılmış olabilir |
| 2026-02-22 | **GUI İyileştirme** | `339a738` | Kaydırılabilir metin alanı, açıklama yeniden düzenleme |
| 2026-02-22 | **React Projesi Kurulumu** | `a04e560` | Vite + TypeScript + Tailwind CSS |
| 2026-02-22 | **Çok Dil Desteği** | `3b481f8` | i18n (Türkçe/İngilizce) |
| 2026-02-22 | **FastAPI Backend** | `08e1303` | REST API, analiz sayfası, CORS |
| 2026-02-22 | **Açıklama API Entegrasyonu** | `1476c63` | API yanıtına explanation alanı eklendi |
| 2026-02-22 | **Etiket Yerelleştirmesi** | `ef0af36` | Duygu/cinsiyet etiketleri dil bazlı |
| 2026-02-22 | **Raporlama Altyapısı** | `bab2958` | run_report.py, confusion matrix, ROC eğrisi |
| 2026-03-12 | **DOCX Rapor Üretici** | `16fa3d3` | Markdown → DOCX dönüştürücü, tez şablonu |
| 2026-03-12 | **Masaüstü Uygulama** | `2a6895c` | PyInstaller, pywebview, Inno Setup, büyük UI güncellemesi |
| 2026-03-12 | **Refactoring + Grafikler** | `72d8a7b` | Kod yapısı, /about sayfası görselleri |
| *2026-03-13 — 2026-04-18* | **Sessiz Dönem (yaklaşık 5 hafta)** | — | Muhtemelen analiz ve karar değerlendirme dönemi |
| 2026-04-19 | **Mimari Sıfırlama** | `5311334` | Eski AI yığını kaldırıldı, README yeniden yazıldı |
| 2026-04-20 | **Yeni Plan** | `fb8602a` | Backend V1 mikro-sprint yürütme planı |
| *2026-04-21 — 2026-05-07* | **Sessiz Dönem (yaklaşık 2.5 hafta)** | — | Yeni sistem kurulumu, yerel geliştirme |
| 2026-05-08 | **Yeni Altyapı (Auto-commit)** | `dc64027` | .env, dataset reorganizasyonu, Claude config |
| 2026-05-10 | **Pseudo-Etiketleme Scriptleri** | `73ff5de` | label_with_*.py, build_manifest_*.py, pipeline scriptleri |
| 2026-05-14 | **Pipeline Çıktıları** | `a846643` | highconf + consensus pipeline manifest'leri |

---

# Zaman Çizelgesi Görsel Özeti

```
2025-11     ████ [Proje başlangıcı: multimodal model + GUI + Grad-CAM]
2025-12     ░░░░ [Sessiz dönem - commitlenmemiş çalışma olabilir]
2026-01     ░░░░ [Sessiz dönem]
2026-02-22  ████████ [YOĞUN SPRINT: React + FastAPI + i18n + Raporlama]
2026-03-12  ████ [Masaüstü paketleme + DOCX + Refactoring]
2026-03     ░░░░ [Sessiz dönem]
2026-04-19  ██ [SIFIRLAMA: Legacy AI kaldırıldı]
2026-04-20  █  [Yeni plan dokümantasyonu]
2026-04     ░░░░ [Sessiz dönem]
2026-05-08  █  [Ortam yapılandırması]
2026-05-10  ██ [Pseudo-etiketleme altyapısı]
2026-05-14  █  [Pipeline çıktıları]
```

---

# Geliştirme Yoğunluğu Analizi

| Dönem | Commit Sayısı | Yoğunluk |
|---|---|---|
| Kasım 2025 | 3 | Düşük (başlangıç) |
| Aralık 2025 – Şubat 2026 | 1 | Çok düşük (sessiz dönem) |
| 22 Şubat 2026 | 7 | **Çok yüksek (tek gün sprinti)** |
| 12 Mart 2026 | 3 | Orta |
| Nisan 2026 | 2 | Düşük (karar dönemi) |
| Mayıs 2026 | 3 | Orta |

---

# Önemli Tarih Notları

1. **22 Şubat 2026 — Kritik Gün:** Projenin en yoğun geliştirme günü. Tek günde React projesi kuruldu, i18n eklendi, FastAPI yazıldı, 6 farklı commit yapıldı. Muhtemelen öncesinde yerel geliştirme yapılmış ve hazır hale gelen kod tek seferde push edilmiştir.

2. **19 Nisan 2026 — Dönüm Noktası:** Eski sistem kaldırıldı. Projenin yaklaşık 5 aylık geliştirme birikiminin önemli bir kısmı devre dışı bırakıldı. Bu karar tez kapsamı açısından kritik öneme sahiptir.

3. **Sessiz Dönemler:** Üç belirgin sessiz dönem mevcuttur. Bu dönemlerde yerel geliştirme, analiz, okuma veya klinisyen görüşmeleri yapılmış olabilir. Commit geçmişi bu dönemleri belgelemez.

---

# Toplam Zaman Dağılımı (Tahmini)

| Aşama | Süre | Dönem |
|---|---|---|
| İlk prototip + GUI | ~2 gün | Kasım 2025 |
| Sessiz dönem | ~3 ay | Aralık 2025 – Şubat 2026 |
| Web + API geliştirme | ~1 gün (yoğun sprint) | Şubat 2026 |
| Masaüstü + Raporlama | ~1 gün | Mart 2026 |
| Karar ve sıfırlama | ~5 hafta | Mart–Nisan 2026 |
| Yeni sistem geliştirme | ~2 hafta | Nisan–Mayıs 2026 |
| **Toplam aktif süre** | **~6 ay** | **Kasım 2025 – Mayıs 2026** |

> Not: Bu tahminler commit tarihlerine dayalıdır. Gerçek çalışma süresi commit yoğunluğundan farklı olabilir.
