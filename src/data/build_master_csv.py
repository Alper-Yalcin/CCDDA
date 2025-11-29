import os
import pandas as pd


BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATASET_DIR = os.path.join(BASE_DIR, "Dataset")
TEXTS_DIR = os.path.join(DATASET_DIR, "Texts")
OUTPUT_CSV = os.path.join(DATASET_DIR, "master_emotion_gender.csv")


def load_emotion(split: str) -> pd.DataFrame:
    """
    Emotion_Train / Emotion_Test dosyalarını okuyup
    id, text_tr, text_en, emotion, split kolonları döndürür.
    """
    if split == "train":
        path = os.path.join(TEXTS_DIR, "Emotion", "Emotion_Train.csv")
    elif split == "test":
        path = os.path.join(TEXTS_DIR, "Emotion", "Emotion_Test.csv")
    else:
        raise ValueError(f"Unknown split: {split}")

    df = pd.read_csv(path)

    # 0: id, 1: tr, 2: en, 3: label, 4: (varsa) Unnamed
    id_col = df.columns[0]
    tr_col = df.columns[1]
    en_col = df.columns[2]
    # label kolonu: 3. sütun, ama ismi "Sadness" vs olabilir
    # Unnamed olmayan ilk 3. indeksteki kolonu al
    label_candidates = [c for c in df.columns[3:] if not c.lower().startswith("unnamed")]
    if not label_candidates:
        raise RuntimeError("Emotion label column not found")
    label_col = label_candidates[0]

    out = df[[id_col, tr_col, en_col, label_col]].copy()
    out.columns = ["id", "text_tr", "text_en", "emotion"]
    out["split"] = split
    return out


def load_gender(split: str) -> pd.DataFrame:
    """
    Gender_Train / Gender_Test dosyalarını okuyup
    id, text_tr, text_en, gender, split kolonları döndürür.
    """
    if split == "train":
        path = os.path.join(TEXTS_DIR, "Gender", "Gender_Train.csv")
    elif split == "test":
        path = os.path.join(TEXTS_DIR, "Gender", "Gender_Test.csv")
    else:
        raise ValueError(f"Unknown split: {split}")

    df = pd.read_csv(path)

    id_col = df.columns[0]
    tr_col = df.columns[1]
    en_col = df.columns[2]
    label_candidates = [c for c in df.columns[3:] if not c.lower().startswith("unnamed")]
    if not label_candidates:
        raise RuntimeError("Gender label column not found")
    label_col = label_candidates[0]

    out = df[[id_col, tr_col, en_col, label_col]].copy()
    out.columns = ["id", "text_tr", "text_en", "gender"]
    out["split"] = split
    return out


def add_image_path(df: pd.DataFrame) -> pd.DataFrame:
    """
    Emotion etiketinden yola çıkarak Emotion images klasöründen img_path üretir.
    Varsayım: her id için resim şu yapıda:
      Dataset/Images/Emotion/<split>/<emotion>/<id>.jpg
    """
    def make_path(row):
        split = row["split"]
        emotion = row["emotion"]
        img_dir = os.path.join(
            DATASET_DIR, "Images", "Emotion", split, emotion
        )
        return os.path.join(img_dir, f"{row['id']}.jpg")

    df["img_path"] = df.apply(make_path, axis=1)
    return df


def main():
    # 1) Emotion + Gender ayrı ayrı yükle
    emo_train = load_emotion("train")
    emo_test = load_emotion("test")
    gen_train = load_gender("train")
    gen_test = load_gender("test")

    # 2) Birleştir
    emo = pd.concat([emo_train, emo_test], ignore_index=True)
    gen = pd.concat([gen_train, gen_test], ignore_index=True)

    # 3) Emotion + Gender'i id + split üzerinden merge et
    merged = pd.merge(
        emo,
        gen[["id", "split", "gender"]],
        on=["id", "split"],
        how="inner",
        validate="one_to_one",
    )

    # 4) Duplicates vs kontrolü (normalde olmamalı)
    merged = merged.drop_duplicates(subset=["id", "split"])

    # 5) Görsel path'i ekle
    merged = add_image_path(merged)

    # 6) Küçük bir sanity check: path var mı?
    missing_files = merged[~merged["img_path"].apply(os.path.exists)]
    if not missing_files.empty:
        print("⚠ Uyarı: Bazı img_path'ler bulunamadı, ilk birkaç satır:")
        print(missing_files.head())
    else:
        print("Tüm img_path'ler mevcut görünüyor.")

    # 7) Kaydet
    os.makedirs(DATASET_DIR, exist_ok=True)
    merged.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
    print(f"Kaydedildi: {OUTPUT_CSV}")
    print("Toplam satır:", len(merged))
    print("Train satır sayısı:", (merged['split'] == 'train').sum())
    print("Test satır sayısı:", (merged['split'] == 'test').sum())


if __name__ == "__main__":
    main()
