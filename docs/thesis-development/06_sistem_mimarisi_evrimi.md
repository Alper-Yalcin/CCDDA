# 06 — Sistem Mimarisi Evrimi

Bu dosya, projenin mimari yapısının zaman içinde nasıl değiştiğini belgeler. Veriler commit geçmişi ve mevcut dosya yapısından elde edilmiştir.

---

## İlk Mimari Yapı (Kasım 2025)

### Dosya Yapısı

```
CCDDA/
├── .gitignore
├── Dataset/
│   └── Images/
│       └── Education/
│           └── test/
│               └── Primary/          ← KIDO veri seti görüntüleri
├── checkpoints/                      ← Model checkpoint'leri
├── notebooks/                        ← Jupyter notebook'lar
└── src/
    ├── data/
    │   ├── dataset.py               ← KidoMultimodalDataset sınıfı
    │   └── transforms.py            ← Görüntü dönüşümleri
    ├── models/
    │   ├── __init__.py
    │   ├── bert_text_only.py        ← Yalnızca metin modeli (boş)
    │   ├── efficientnet_multitask.py ← Yalnızca görüntü modeli (boş)
    │   └── multimodal_effnet_bert.py ← Ana model: EfficientNet + BERT
    └── train/
        └── train_multimodal.py      ← Eğitim scripti
```

### Mimari Diyagramı

```
Görüntü → EfficientNet-B0 → AdaptiveAvgPool2d → [B, 1280]
                                                      ↓
                                               img_proj (Linear 1280→512)
                                                      ↓
Metin  → Türkçe BERT → [CLS] token → [B, 768]        ↓
                                          ↓       Concat [B, 1024]
                                 text_proj (Linear 768→512)     ↓
                                                         ↓
                                              Emotion Head (1024→2)
                                              Gender Head  (1024→2)
```

### Özellikler
- **Veri**: KIDO veri seti, ikili etiket (Happiness/Sadness + Female/Male)
- **Model**: 116M parametre, 5.6M eğitilebilir
- **Kullanıcı arayüzü**: Henüz yok
- **Eğitim**: `python src/train/train_multimodal.py`

---

## Birinci Genişleme: Açıklanabilirlik + GUI (Kasım 2025)

### Yeni Bileşenler (`d494e7b`)

```
src/
├── app/
│   ├── gui_multimodal.py    ← Ana Tkinter GUI (tam özellikli)
│   └── tk_app.py            ← Daha sade Tkinter sarmalayıcı
├── explain/
│   ├── gradcam.py           ← Grad-CAM görselleştirme
│   ├── perception_api.py    ← Harici görsel analiz API istemcisi
│   ├── predict_and_explain.py ← Tahmin + açıklama pipeline'ı
│   ├── rule_based_explainer.py ← Kural tabanlı açıklayıcı
│   └── text_explain.py      ← Metin tabanlı açıklama üretici
└── data/
    └── dataset.py           ← Genişletildi
```

### Mimari Durumu

```
[Model Inference]
      ↓
[Grad-CAM] → görsel ısı haritası
      ↓
[Rule-Based Explainer] → açıklama metni
      ↓
[Tkinter GUI] → kullanıcıya gösterim
```

---

## İkinci Genişleme: Web + FastAPI (Şubat 2026)

### Yeni Bileşenler (`a04e560` – `bab2958`)

```
CCDDA/
├── api_server.py            ← FastAPI REST API (YENİ)
├── requirements.txt         ← FastAPI bağımlılıkları eklendi
└── Web/                     ← React projesi (YENİ)
    ├── .env.example
    ├── index.html
    ├── package.json
    ├── vite.config.ts       ← Proxy yapılandırması
    └── src/
        ├── App.tsx          ← Ana React bileşeni
        ├── main.tsx
        ├── index.css
        └── locales/
            ├── tr.json      ← Türkçe çeviriler
            └── en.json      ← İngilizce çeviriler
```

### Mimari Durumu

```
[React Arayüz (port 3000)]
          ↓ HTTP POST /predict (Vite proxy)
[FastAPI Backend (port 8000)]
          ↓
[src.explain.predict_and_explain]
          ↓
[EfficientNet-B0 + BERT Model]
          ↓
[Rule-Based / LLM Explainer]
          ↑
[GITHUB_TOKEN → GitHub Models API (opsiyonel)]
```

### API Endpoint'leri (İlk Versiyon)
- `GET /health` — Sunucu sağlık kontrolü
- `POST /predict` — Görüntü + metin gönder, tahmin + açıklama al

---

## Üçüncü Genişleme: Masaüstü Paketleme + Raporlama (Mart 2026)

### Yeni Bileşenler (`16fa3d3`, `2a6895c`, `72d8a7b`)

```
CCDDA/
├── desktop_app.py           ← FastAPI + pywebview sarmalayıcı (YENİ)
├── desktop_app.spec         ← PyInstaller yapılandırması (YENİ)
├── src/
│   └── app_paths.py         ← Paketlenmiş ortamda yol çözücü (YENİ)
├── build/                   ← PyInstaller ara çıktılar
├── dist/                    ← Derleme çıktıları (.exe)
├── installer/               ← Inno Setup ve kurulum betikleri
├── build_report_docx.py     ← Markdown → DOCX dönüştürücü (YENİ)
└── Web/
    └── public/
        └── about/           ← Performans grafikleri (YENİ)
            ├── confusion-matrices.png
            ├── roc-curves.png
            ├── sample-predictions.png
            └── training-curves.png
```

### Dağıtım Seçenekleri

```
┌─────────────────────────────────────────────┐
│              Dağıtım Modları                │
├──────────────────┬──────────────────────────┤
│  Web Modu        │  Masaüstü Modu            │
│  React + FastAPI │  desktop_app.py           │
│  Ayrı sunucular  │  PyInstaller .exe         │
│  Tarayıcı gerekir│  Kendi kendine yeten      │
└──────────────────┴──────────────────────────┘
```

---

## Kritik Sıfırlama: Legacy AI Temizleme (Nisan 2026)

### Kaldırılan Bileşenler (`5311334`)

Kaldırılan bileşenler (README.md'den):
- `emotion + gender çok görevli sınıflandırma` sistemi
- `BERT tabanlı multimodal akış`
- Eski checkpoint'ler
- Eski explainability ve inference kodları
- Büyük eğitim veri seti (`Dataset/Images/Education/`)

### Korunan Bileşenler

```
CCDDA/                       ← Korunan
├── Web/                     ← React + i18n arayüzü
├── desktop_app.py           ← Masaüstü sarmalayıcı
├── api_server.py            ← FastAPI (503 döndürüyor)
├── src/
│   ├── app/                 ← GUI modülleri
│   ├── data/                ← Dönüşüm yardımcıları
│   ├── explain/             ← Açıklanabilirlik modülleri
│   └── utils/               ← Genel araçlar
└── docs/                    ← Dokümantasyon
```

### API Durumu (Nisan 2026 sonrası)
```python
# api_server.py — /predict endpoint durumu
"reset_in_progress" → HTTP 503
```

---

## Son Mimari Yapı (Mayıs 2026 — Aktif Geliştirme)

### Tam Dosya Yapısı

```
CCDDA/
├── api_server.py               ← FastAPI (503 modunda)
├── desktop_app.py              ← Masaüstü sarmalayıcı (korundu)
├── requirements.txt            ← Güncel bağımlılıklar
│
├── Dataset/
│   ├── Images/
│   │   ├── Emotion_4Class/     ← YENİ: 4-sınıf etiketli veri
│   │   │   ├── Anger/
│   │   │   ├── Fear/
│   │   │   ├── Happy/
│   │   │   └── Sad/
│   │   ├── Emotion_Roboflow_DrawingFacialEmotions/
│   │   ├── Emotion_SigLIP_4Class/
│   │   ├── GoldTest_Candidates_Auto4Class/
│   │   └── Education/          ← Orijinal KIDO
│   ├── Texts/
│   └── huggingface/            ← Parquet veri kümesi
│
├── out/
│   ├── highconf_pipeline/      ← YENİ: Yüksek güvenilirlik çıktıları
│   │   ├── manifests/
│   │   │   ├── manifest_highconf_075.csv  (~23K örnek)
│   │   │   └── manifest_highconf_085.csv  (~19K örnek)
│   │   └── teacher_labels_all.csv
│   └── consensus_pipeline/     ← YENİ: Uzlaşma çıktıları
│       ├── manifests/
│       │   └── manifest_consensus_3of3_c060.csv
│       └── teacher_b_b3_075_labels_all.csv
│
├── artifacts/                  ← Model checkpoint'leri ve raporlar
├── build_manifest_*.py         ← Veri manifesti scriptleri (çok sayıda)
├── label_with_*.py             ← Pseudo-etiketleme scriptleri
├── run_highconf_pipeline.py    ← Ana high-conf pipeline
├── run_consensus_pipeline.py   ← Ana consensus pipeline
├── eval_test.py                ← Değerlendirme
├── eval_tta.py                 ← Test-time augmentation değerlendirme
│
└── Web/                        ← React arayüz (korundu)
    └── src/
        └── locales/
            ├── tr.json
            └── en.json
```

### Yeni AI Mimarisi (Hedef)

```
[Etiketsiz Görüntüler]
         ↓
[Öğretmen Model: EfficientNet-B3]
         ↓ (güven > 0.75)
[Pseudo-Etiketler]
         ↓ consensus filtresi
[Yüksek Kaliteli Manifest]
         ↓
[Öğrenci Model: EfficientNet-B3 (yeni eğitim)]
         ↓
[FastAPI /predict] → [React UI]
```

---

## Mimari Değişikliklerin Yorumu

Projenin mimari evrimi üç ana eksen üzerinde gerçekleşmiştir:

1. **Model karmaşıklığı ekseni**: Çok modlu (görüntü+metin) → Tek modlu (yalnızca görüntü). Bu sadeleşme, araştırma odağını netleştirmiş ve veri gereklilikleri azaltmıştır.

2. **Arayüz ekseni**: Tkinter (yerel) → React Web → React+PyInstaller (çift mod). Arayüzün evriminin her adımı daha geniş erişilebilirlik sunmaktadır.

3. **Veri stratejisi ekseni**: Sabit küçük veri seti → Çok kaynaklı + pseudo-etiketleme. Bu geçiş, etiketli veri kıtlığı sorununa yönelik sistematik bir çözümü temsil etmektedir.

### Tezde Kullanılabilecek Anlatım

Sistem mimarisi, üç temel evrimsel aşamadan geçmiştir. İlk aşamada çok modlu bir mimari denenmiş; ikinci aşamada web tabanlı dağıtıma geçilmiş; üçüncü ve güncel aşamada ise yalnızca görüntü tabanlı, pseudo-etiketleme destekli 4-sınıflı bir mimari benimsenmiştir. Bu evrim, hem teknik deneyimden hem de araştırma sorusunun yeniden çerçevelenmesinden beslenmektedir.
