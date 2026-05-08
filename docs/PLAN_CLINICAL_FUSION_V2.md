# Plan: Klinik Özellik Entegrasyonlu 4-Sınıf Duygu Sınıflandırma Sistemi

## Context

Mevcut CCDDA projesi sıfırlandı (commit `5311334`): eski 2-sınıflı çok-modlu (EfficientNet-B0 + BERTurk) yığın kaldırıldı, `api_server.py` `/predict` uç noktası 503 döndürüyor. Artık elimizde:

- **Yeni veri seti**: `Dataset/Images/Emotion_SigLIP_4Class_Filtered_045` — SigLIP ile otomatik etiketlenmiş 4 sınıflı (Happy, Sad, Angry, Fear), train=7088 / test=1262. Etiketler insan tarafından değil, `google/siglip-base-patch16-224` tarafından üretilmiş ve 0.45 güven eşiğiyle filtrelenmiş.
- **İki araştırma raporu**: Klinik psikoloji + CV mühendisliği — 18+ ölçülebilir klinik özellik tanımlıyor.
- **Var olan web altyapısı**: FastAPI (`api_server.py`), React SPA (`Web/src/App.tsx`), PyWebView desktop sarıcı (`desktop_app.py`) — hazır ama modelsiz.
- **Git geçmişinde (commit `2a6895c`)**: Eski Grad-CAM (`src/explain/gradcam.py`), dataset loader, training loop. Referans ve yeniden kullanım için erişilebilir.

**Hedeflenen sonuç**: SigLIP etiketlerinin yüzeysel (klinik olmayan) doğası nedeniyle, modelin sadece piksel değil, aynı zamanda **klinik olarak anlamlı özellik vektörü** üzerinden de karar vermesi. Grad-CAM ile modelin baktığı bölge görselleştirilecek ve GitHub Models token'ı üzerinden GPT-4o ile doğal dil açıklaması üretilecek. Tüm sistem mevcut web/desktop arayüzüne entegre edilecek.

---

## Mimari Genel Bakış

```
Çizim Yüklendi
    ├──► EfficientNet-B0 (ImageNet pretrained, 1280-dim)
    │        └──► Proje → 256-dim
    │
    ├──► OpenCV Klinik Özellik Çıkarıcı (18 özellik + validity mask)
    │        └──► MLP → 64-dim
    │
    └──► Fusion (Concat → 320-dim) → MLP → 4 logit
                                          │
                     ┌────────────────────┼───────────────────┐
                     ▼                    ▼                   ▼
               Softmax probs        Grad-CAM heatmap    Klinik feature
                                                          dictionary
                              │
                              ▼
                     GitHub Models (GPT-4o)
                     → Doğal dil açıklama (TR/EN)
```

---

## Dosya Yapısı (Uygulanacak)

```
src/
├── data/
│   ├── transforms.py              # mevcut, kullanılacak
│   ├── dataset.py                 # YENİ — SigLIPDrawingDataset
│   └── build_manifest.py          # YENİ — SigLIP klasör yapısından manifest
├── features/
│   ├── __init__.py                # YENİ
│   ├── clinical_extractor.py      # YENİ — OpenCV feature extraction
│   └── feature_spec.py            # YENİ — feature listesi + validity
├── models/
│   ├── __init__.py                # mevcut (boş)
│   ├── efficientnet_backbone.py   # YENİ — image encoder wrapper
│   └── fusion_classifier.py       # YENİ — ana model
├── train/
│   └── train_image_only.py        # mevcut (boş) — YENİDEN YAZILACAK
├── eval/
│   └── evaluate.py                # YENİ
├── explain/
│   ├── __init__.py                # mevcut (boş)
│   ├── gradcam.py                 # YENİ (git commit 2a6895c'den adapte)
│   └── llm_explainer.py           # YENİ — GitHub Models istemcisi
└── inference/
    └── pipeline.py                # YENİ — tüm adımları birleştiren servis

api_server.py                       # mevcut — /predict gerçek inference ile güncellenecek
Web/src/App.tsx                     # mevcut — gender alanları gizlenecek, klinik özellik paneli eklenecek
Web/src/i18n/en.json                # yeni metin anahtarları
Web/src/i18n/tr.json                # yeni metin anahtarları
artifacts/v1_backend/               # YENİ çıktı dizini
├── data/manifest.csv
├── features/features_v1.csv
├── train/checkpoints/best.pt
├── train/train_history.json
├── eval/metrics.json
├── eval/predictions_test.csv
└── eval/confusion_matrix.csv
```

---

## Uygulama Adımları

### 1. Manifest ve Dataset (`src/data/`)

**`src/data/build_manifest.py`**: `Dataset/Images/Emotion_SigLIP_4Class_Filtered_045/{train,test}/{Happy,Sad,Angry,Fear}/*` klasör yapısını tarayıp `artifacts/v1_backend/data/manifest.csv` üretir. Sütunlar:
- `sample_id` (dosya adından türet), `image_path`, `label` (string), `label_id` (0-3), `split` (train/val/test), `sha256`, `width`, `height`
- Train'in %15'i stratified olarak val'e ayrılır (`seed=42`)
- `Dataset/Texts/Emotion_SigLIP_4Class_Filtered_045/predictions_filtered.csv`'den SigLIP soft-label skorları (`score_Happy`, `score_Sad`, `score_Angry`, `score_Fear`, `confidence`) join edilir — bunlar auxiliary bilgi olarak saklanır
- SHA-256 çakışma kontrolü (farklı sınıfta aynı hash var mı?) — sert başarısızlık

**`src/data/dataset.py`**: `SigLIPDrawingDataset(Dataset)` sınıfı. `__getitem__` geri döner:
```python
{
    "image": torch.Tensor,              # 224x224x3
    "clinical_features": torch.Tensor,  # 18-dim (veya offline precomputed)
    "clinical_validity": torch.Tensor,  # 18-dim 0/1 mask
    "label": int,
    "sample_id": str,
}
```
Transforms `src/data/transforms.py`'den gelir. Train'de `HorizontalFlip` **kaldırılır** (klinik raporlara göre sol/sağ yerleşim anlam taşır).

### 2. Klinik Özellik Çıkarıcı (`src/features/`)

**`src/features/feature_spec.py`**: Plan.md'deki ve raporlardaki özellik listesi — tam 18 özellik:

| Özellik | Hesaplama |
|---|---|
| `fg_area_ratio` | Foreground piksel / toplam |
| `empty_space_ratio` | 1 - fg_area_ratio |
| `bbox_area_ratio` | En büyük component bbox / canvas |
| `centroid_x_norm`, `centroid_y_norm` | Image moments |
| `top_mass_ratio`, `bottom_mass_ratio` | Yarım bölme |
| `stroke_darkness_mean`, `stroke_darkness_std` | Foreground luma istatistikleri |
| `component_count_norm` | Connected components / (area/10k) |
| `skeleton_break_count_norm` | Skeleton endpoint sayısı |
| `shading_ratio` | Yoğun koyu bölge oranı |
| `unique_hue_count` | HSV hist benzersiz hue |
| `warm_ratio`, `dark_color_ratio` | HSV band kuralı |
| `sharp_angle_ratio` | Contour keskin köşe oranı |
| `dominant_orientation_abs` | PCA ana eksen (normalize) |
| `face_candidate_count` | Heuristic yüz aday sayısı |
| `figure_integrity_proxy` | Component + extension composite |

Her özellik için `*_valid` flag. Invalid durumda NaN + 0 bayrak.

**`src/features/clinical_extractor.py`**: Tek bir fonksiyon `extract_clinical_features(image_pil) -> (features: np.ndarray[18], validity: np.ndarray[18])`. OpenCV operasyonları:
- Grayscale + adaptive threshold → foreground mask
- `cv2.connectedComponentsWithStats` → component metrikleri
- `cv2.findContours` + `cv2.approxPolyDP` → açısal analiz
- HSV space → renk metrikleri
- Morphological skeleton → endpoint sayısı (cv2 tabanlı ya da skimage fallback)

**Batch çıkarım aracı**: Training öncesi tüm veri seti için tek seferlik `artifacts/v1_backend/features/features_v1.csv` üretilir. Training'de offline lookup, inference'da runtime çıkarım.

### 3. Model (`src/models/`)

**`src/models/efficientnet_backbone.py`**: `torchvision.models.efficientnet_b0(weights=IMAGENET1K_V1)`. Classifier kaldırılır, pooled 1280-dim vektör döner. Son conv bloğuna hook eklenir (Grad-CAM için).

**`src/models/fusion_classifier.py`**:
```python
class ClinicalFusionClassifier(nn.Module):
    def __init__(self, num_classes=4, feat_dim=18):
        self.image_backbone = EfficientNetBackbone()      # -> 1280
        self.image_proj = nn.Linear(1280, 256)
        self.clinical_mlp = nn.Sequential(
            nn.Linear(feat_dim * 2, 128),  # özellik + validity concat
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 64),
            nn.ReLU(),
        )
        self.fusion = nn.Sequential(
            nn.Linear(256 + 64, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes),
        )

    def forward(self, image, clinical, validity):
        img_feat = self.image_proj(self.image_backbone(image))
        clin_feat = self.clinical_mlp(torch.cat([clinical, validity], dim=-1))
        return self.fusion(torch.cat([img_feat, clin_feat], dim=-1))
```

Eksik klinik özellik durumunda (validity=0) klinik dal zaten zayıflar, ama son güven elleşmesi fusion katmanında öğrenilir.

### 4. Eğitim (`src/train/train_image_only.py`)

- **Loss**: `CrossEntropyLoss(weight=class_weights)` — class weight ters-frekans
- **Sampler**: `WeightedRandomSampler` (Angry:361 ↔ Happy:3459 için)
- **Optimizer**: AdamW, lr=1e-4, weight_decay=1e-4
- **Scheduler**: CosineAnnealingLR, T_max=30
- **Epochs**: 30, early stopping patience=7
- **Best checkpoint kriteri**: `val_macro_f1`
- **Deterministik**: `seed=42`
- **Çıktılar**:
  - `artifacts/v1_backend/train/checkpoints/best.pt` (model state, optimizer, epoch, val_macro_f1)
  - `artifacts/v1_backend/train/train_history.json` (per-epoch train/val loss, acc, macro_f1)
  - `artifacts/v1_backend/train/config_snapshot.json` (hyperparams)

**CLI**:
```bash
python -m src.train.train_image_only \
  --manifest artifacts/v1_backend/data/manifest.csv \
  --features artifacts/v1_backend/features/features_v1.csv \
  --out artifacts/v1_backend/train \
  --epochs 30 --batch-size 32 --seed 42
```

### 5. Değerlendirme (`src/eval/evaluate.py`)

- Metrics: `accuracy`, `macro_f1`, `balanced_accuracy`, per-class P/R/F1, confusion matrix
- `predictions_test.csv`: `sample_id, true_label, pred_label, top1_conf, top2_conf, entropy, probs_json`
- ECE (10 bin) kalibrasyon
- Error analysis CSV (`misclassified.csv`, `high_confidence_errors.csv`)

### 6. Grad-CAM (`src/explain/gradcam.py`)

Git `commit 2a6895c` içindeki `src/explain/gradcam.py`'i referans al, **image-only backbone için uyarla**:
- Target layer: `efficientnet_b0.features[-1]` (son conv)
- Forward/backward hooks
- Output: 224x224 normalized CAM + JET colormap overlay (PIL Image veya base64 PNG)

```python
def generate_gradcam(model, image_tensor, clinical, validity, target_class=None) -> np.ndarray:
    ...
```

### 7. GitHub Models LLM Açıklayıcı (`src/explain/llm_explainer.py`)

OpenAI SDK formatında GitHub Models endpoint:

```python
import os
from openai import OpenAI

class LLMExplainer:
    def __init__(self):
        self.client = OpenAI(
            base_url="https://models.inference.ai.azure.com",
            api_key=os.environ["GITHUB_TOKEN"],
        )
        self.model = "gpt-4o"  # ya da "gpt-4o-mini" (daha hızlı)

    def explain(
        self,
        predicted_label: str,
        probs: dict[str, float],
        clinical_features: dict[str, float],
        clinical_validity: dict[str, bool],
        gradcam_summary: str,  # örn. "figürün sol alt köşesi"
        lang: str = "tr",
    ) -> str:
        system = build_system_prompt(lang)  # klinik psikoloji raporunu özetleyen
        user = build_user_prompt(predicted_label, probs, clinical_features, ...)
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.3,
            max_tokens=400,
        )
        return resp.choices[0].message.content
```

**Sistem prompt**: İki raporun (`Saf Klinik Psikoloji ve Projektif Testler Odaklı Rapor.md`, `Mühendislik ve CV (Bilgisayarlı Görü) Odaklı Rapor.md`) öz bilgisini içerir. Model, klinik özellik değerlerini ve Grad-CAM bölgesini gerekçelendirerek 3-4 cümlelik tutarlılık açıklaması yazar. "Klinik tanı değildir" uyarısı zorunlu.

**Grad-CAM özetleyici**: Heatmap'in argmax bölgesini (üst-sol, alt-sol, merkez, vb.) sözel karşılığına çevirir — ayrı yardımcı fonksiyon, LLM'e açıklama değil koordinat vermemek için.

**Fallback**: Token yoksa ya da API hata döndürürse kural tabanlı deterministik açıklama üretir (`src/explain/rule_based_explainer.py`) — klinik feature değerlerinden template text.

**Env**: `GITHUB_TOKEN` env var'dan okunur; `.env` dosyası desteklenir (python-dotenv eklenecek).

### 8. Inference Pipeline (`src/inference/pipeline.py`)

Tek bir `InferencePipeline` sınıfı — model bir kere yükler, tekrar tekrar kullanılır:

```python
class InferencePipeline:
    def __init__(self, checkpoint_path, device="cpu"):
        self.model = load_model(checkpoint_path, device)
        self.extractor = ClinicalFeatureExtractor()
        self.gradcam = GradCAM(self.model)
        self.llm = LLMExplainer()
        self.class_names = ["Happy", "Sad", "Angry", "Fear"]

    def predict(self, image_pil: Image, lang: str = "tr") -> dict:
        clinical, validity = self.extractor.extract(image_pil)
        image_tensor = preprocess(image_pil)
        with torch.no_grad():
            logits = self.model(image_tensor, clinical_tensor, validity_tensor)
            probs = softmax(logits)
        pred_idx = probs.argmax()
        heatmap_b64 = self.gradcam.generate_overlay(image_tensor, pred_idx)
        explanation = self.llm.explain(
            predicted_label=self.class_names[pred_idx],
            probs={n: float(probs[i]) for i, n in enumerate(self.class_names)},
            clinical_features=dict(zip(FEATURE_NAMES, clinical)),
            clinical_validity=dict(zip(FEATURE_NAMES, validity)),
            gradcam_summary=summarize_cam_region(heatmap_raw),
            lang=lang,
        )
        return {
            "pred_emotion": self.class_names[pred_idx],
            "confidence_emotion": float(probs[pred_idx]),
            "probs_emotion": probs.tolist(),
            "heatmap_emotion_b64": heatmap_b64,
            "explanation": explanation,
            "clinical_features": {...},  # frontend için gösterilebilir
        }
```

### 9. API Entegrasyonu (`api_server.py`)

Mevcut dosya güncellenecek:
- `create_app()` içinde `lifespan` → pipeline yükler (`preload_model=True` ise)
- `/predict` artık 503 değil, gerçek JSON döner
- Response şeması, mevcut frontend `ApiResult` ile uyumlu (hata çıkmaması için):
  - `pred_emotion`, `confidence_emotion`, `probs_emotion`, `heatmap_emotion_b64`, `explanation`
  - `pred_gender`, `confidence_gender`, `heatmap_gender_b64`, `tokens_*` → boş/null (frontend back-compat var)
  - **Yeni alanlar**: `clinical_features` (dict), `clinical_validity` (dict), `class_names` (["Happy","Sad","Angry","Fear"])
- Hata yönetimi: LLM başarısızlığında rule-based fallback çalışır; 200 döner.

### 10. Frontend (`Web/src/App.tsx` + i18n)

Minimal değişiklikler:
- `ApiResult` tipi genişletilir (`clinical_features`, `clinical_validity`, `class_names`)
- Gender bölümleri kaldırılır veya gizlenir
- Yeni "Klinik Özellikler" paneli: high-confidence bloktaki 5-6 metrik bar chart olarak gösterilir (fg_area_ratio, stroke_darkness, shading_ratio, component_count, sharp_angle)
- `tr.json` / `en.json` yeni metin anahtarları (feature isimlerinin yerel karşılıkları)
- 4 sınıf olasılık bar'ı (Happy, Sad, Angry, Fear)

### 11. Desktop App (`desktop_app.py`)

Değişiklik yok — FastAPI'yi aynı şekilde başlatır. Env'den `GITHUB_TOKEN` taşınması için `os.environ` kopyalama kontrolü.

### 12. Requirements

`requirements.txt`'e ekle:
- `openai>=1.0.0` (GitHub Models SDK uyumlu)
- `python-dotenv`
- `timm` (EfficientNet varyantları için, opsiyonel)
- `grad-cam` (opsiyonel — kendi implementasyonumuz varsa gerekmez)

---

## Kritik Dosyalar (Değişecek)

| Dosya | Durum | Amaç |
|---|---|---|
| `api_server.py` | Güncelle | Gerçek pipeline'ı yükle + /predict |
| `src/data/build_manifest.py` | Yeni | SigLIP dataset'ten manifest |
| `src/data/dataset.py` | Yeni | SigLIPDrawingDataset |
| `src/data/transforms.py` | Güncelle | HorizontalFlip çıkar |
| `src/features/feature_spec.py` | Yeni | 18 özellik tanımı |
| `src/features/clinical_extractor.py` | Yeni | OpenCV extractor |
| `src/models/efficientnet_backbone.py` | Yeni | Backbone wrapper |
| `src/models/fusion_classifier.py` | Yeni | Ana model |
| `src/train/train_image_only.py` | Yeniden yaz | Eğitim döngüsü |
| `src/eval/evaluate.py` | Yeni | Metrik + error analysis |
| `src/explain/gradcam.py` | Yeni | Grad-CAM (git 2a6895c adapte) |
| `src/explain/llm_explainer.py` | Yeni | GitHub Models istemcisi |
| `src/explain/rule_based_explainer.py` | Yeni | Fallback açıklayıcı |
| `src/inference/pipeline.py` | Yeni | Uçtan uca servis |
| `Web/src/App.tsx` | Güncelle | Klinik panel + gender gizle |
| `Web/src/i18n/{tr,en}.json` | Güncelle | Yeni metin anahtarları |
| `requirements.txt` | Güncelle | openai, python-dotenv |
| `.env.example` | Yeni | GITHUB_TOKEN placeholder |

---

## Yeniden Kullanılacak (Git Geçmişinden — commit `2a6895c`)

- `src/explain/gradcam.py` — hook yapısı + colormap (image-only için sadeleştirilerek adapte)
- `src/models/efficientnet_multitask.py` — EfficientNet wrapper pattern referansı
- `src/data/dataset.py` (eski) — Dataset class pattern referansı

---

## Verification

### Yerel Test Sırası

1. **Manifest oluştur** ve 8350 satır, 4 sınıf dağılımını doğrula:
   ```bash
   python -m src.data.build_manifest \
     --images-root Dataset/Images/Emotion_SigLIP_4Class_Filtered_045 \
     --predictions Dataset/Texts/Emotion_SigLIP_4Class_Filtered_045/predictions_filtered.csv \
     --out artifacts/v1_backend/data/manifest.csv \
     --val-ratio 0.15 --seed 42
   ```

2. **Feature extraction smoke test** (10 örnek):
   ```bash
   python -m src.features.clinical_extractor --test-sample 10
   # Her özellik için değer + validity kontrol
   ```

3. **Tüm dataset için batch feature extraction**:
   ```bash
   python -m src.features.clinical_extractor \
     --manifest artifacts/v1_backend/data/manifest.csv \
     --out artifacts/v1_backend/features/features_v1.csv
   ```

4. **Training** (önce 3 epoch smoke test, sonra tam 30):
   ```bash
   python -m src.train.train_image_only --epochs 3 --batch-size 16  # smoke
   python -m src.train.train_image_only --epochs 30 --batch-size 32 # full
   ```

5. **Evaluation**:
   ```bash
   python -m src.eval.evaluate \
     --ckpt artifacts/v1_backend/train/checkpoints/best.pt \
     --out artifacts/v1_backend/eval
   ```
   Başarı eşiği: `val_macro_f1 > 0.70` (class imbalance + noisy label nedeniyle gerçekçi).

6. **Pipeline end-to-end test** (tek görüntü ile):
   ```bash
   python -c "from src.inference.pipeline import InferencePipeline; \
              p = InferencePipeline('artifacts/v1_backend/train/checkpoints/best.pt'); \
              from PIL import Image; \
              r = p.predict(Image.open('Dataset/Images/.../sample.jpg'), lang='tr'); \
              print(r['pred_emotion'], r['explanation'])"
   ```

7. **API testi**:
   ```bash
   export GITHUB_TOKEN=...
   uvicorn api_server:app --host 0.0.0.0 --port 8000
   curl -F "image=@sample.jpg" -F "lang=tr" http://localhost:8000/api/predict
   ```
   Beklenen: 200 + `pred_emotion`, `confidence_emotion`, `heatmap_emotion_b64`, `explanation`, `clinical_features` içeren JSON.

8. **Frontend testi**: `Web/` içinde `npm run dev`, çizim yükle, klinik özellik paneli + heatmap + LLM açıklaması görünmeli. Dil değiştirme butonu açıklamayı TR/EN yeniden üretmeli.

9. **Desktop paket testi**: `python desktop_app.py` — WebView aynı davranışı sergilemeli.

### Kabul Kriterleri

- Manifest: 8350 satır, train/val/test bölünmesi stratified, çakışma yok
- Training: `best.pt` üretilir, `val_macro_f1 > 0.70`
- Feature CSV: 8350 satır, 18 feature + 18 validity sütunu
- API `/predict`: `200 OK`, `pred_emotion ∈ {Happy, Sad, Angry, Fear}`, heatmap base64, explanation non-empty string
- Frontend: Klinik feature paneli render edilir, Grad-CAM overlay görünür, LLM açıklama gösterilir
- LLM fallback: `GITHUB_TOKEN` boş olsa bile `/predict` 200 döner, rule-based açıklama ile
- Dil: `lang=tr` → Türkçe açıklama, `lang=en` → İngilizce açıklama

---

## Riskler ve Notlar

1. **SigLIP etiket kalitesi**: Etiketler klinik değil, yüzeysel. Klinik özellik vektörü tam da bu nedenle kritik — modelin denetim katmanı işlevi görüyor. Değerlendirme raporunda bu sınırlılık açıkça belirtilecek.
2. **Class imbalance (Angry:361 vs Happy:3459)**: WeightedRandomSampler + class weights yeterli olmazsa, Angry için oversampling + augmentation fallback'ı olabilir.
3. **GitHub Models rate limit**: Ücretsiz tier sınırlı. Yüksek hacim için istek cache'leme (aynı `sample_id + lang` için) eklenebilir.
4. **Grad-CAM sanity**: Boş/çok beyaz görüntülerde aşırı güven problemi olabilir — evaluation'da bu ayrı track edilecek.
5. **Yaş/görev tipi**: CV raporu yaş normalizasyonunu zorunlu kılıyor, ancak mevcut veri setinde yaş yok. Bu V1 için ertelenmiş kabul edilir; açıklamalarda belirtilir.
