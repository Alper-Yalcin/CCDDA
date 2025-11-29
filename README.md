# RUN
python src/data/build_master_csv.py
python -m src.train.train_multimodal --epochs 5 --batch_size 8
# venv kullanıyorsan
python -m venv .venv
source .venv/bin/activate 
.venv\Scripts\activate

# KIDO Multimodal Emotion & Gender Analysis

Bu proje, **KIDO** veri setini kullanarak çocukların çizimlerinden:
- Çizen kişinin **cinsiyetini** (Male / Female),
- Çocuğun **duygu durumunu** (Happiness / Sadness),

hem **görsel** (çizim) hem de **metin** (çocuğun yazdığı açıklama) üzerinden tahmin etmeyi ve  
bu tahminleri **açıklanabilir** hale getirmeyi amaçlayan çok-modlu (multi-modal), çok-görevli (multi-task) bir derin öğrenme modelini içerir.

Ana mimari:
- 🖼 **EfficientNet-B0** → çizimden görsel özellik çıkarma
- 📝 **BERTurk / mBERT** → metinden dil özellikleri çıkarma
- 🔗 Birleştirme (fusion) → ortak temsil
- 🎯 2 ayrı head → **Emotion** + **Gender** sınıflandırma
- 🧠 **Grad-CAM + attention** ile açıklanabilirlik

---

## 1. Proje Yapısı

Önerilen klasör yapısı:

```text
kido_multimodal/
├─ Dataset/
│  ├─ Images/
│  │  ├─ Education/
│  │  │  ├─ train/
│  │  │  │  ├─ Primary/
│  │  │  │  └─ Secondary/
│  │  │  └─ test/
│  │  │     ├─ Primary/
│  │  │     └─ Secondary/
│  │  ├─ Emotion/
│  │  │  ├─ train/
│  │  │  │  ├─ Happiness/
│  │  │  │  └─ Sadness/
│  │  │  └─ test/
│  │  │     ├─ Happiness/
│  │  │     └─ Sadness/
│  │  ├─ Gender/
│  │  │  ├─ train/
│  │  │  │  ├─ Female/
│  │  │  │  └─ Male/
│  │  │  └─ test/
│  │  │     ├─ Female/
│  │  │     └─ Male/
│  └─ Texts/
│     ├─ Education/
│     │  ├─ Education_Train.csv
│     │  └─ Education_Test.csv
│     ├─ Emotion/
│     │  ├─ Emotion_Train.csv
│     │  └─ Emotion_Test.csv
│     └─ Gender/
│        ├─ Gender_Train.csv
│        └─ Gender_Test.csv
├─ src/
│  ├─ data/
│  │  ├─ build_master_csv.py
│  │  ├─ dataset.py
│  │  └─ transforms.py
│  ├─ models/
│  │  ├─ efficientnet_multitask.py
│  │  ├─ bert_text_only.py
│  │  └─ multimodal_effnet_bert.py
│  ├─ train/
│  │  ├─ train_image_only.py
│  │  ├─ train_text_only.py
│  │  └─ train_multimodal.py
│  ├─ eval/
│  │  └─ evaluate.py
│  └─ explain/
│     └─ gradcam_and_text_explain.py
├─ notebooks/
│  └─ EDA_and_sanity_checks.ipynb
├─ requirements.txt
└─ README.md
