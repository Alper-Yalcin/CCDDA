import os
from typing import Optional, Callable, Dict, Any

import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset


EMOTION_MAP = {"Happiness": 0, "Sadness": 1}
GENDER_MAP = {"Female": 0, "Male": 1}


class KidoMultimodalDataset(Dataset):
    def __init__(
        self,
        csv_path: str,
        split: str,
        tokenizer,
        image_transform: Optional[Callable] = None,
        max_length: int = 128,
        use_english: bool = False,
    ):
        """
        csv_path: Dataset/master_emotion_gender.csv
        split: "train" / "test" (val'ı train içinden böleceğiz)
        tokenizer: BERT tokenizer (örn: BERTurk)
        image_transform: torchvision transforms
        """
        super().__init__()

        if not os.path.exists(csv_path):
            raise FileNotFoundError(csv_path)

        self.df = pd.read_csv(csv_path)

        # split filtresi
        self.df = self.df[self.df["split"] == split].reset_index(drop=True)

        self.tokenizer = tokenizer
        self.image_transform = image_transform
        self.max_length = max_length
        self.use_english = use_english

        # Label map
        self.df["emotion_id"] = self.df["emotion"].map(EMOTION_MAP)
        self.df["gender_id"] = self.df["gender"].map(GENDER_MAP)

        if self.df["emotion_id"].isna().any():
            missing = self.df[self.df["emotion_id"].isna()]["emotion"].unique()
            raise ValueError(f"Bilinmeyen emotion label(lar): {missing}")
        if self.df["gender_id"].isna().any():
            missing = self.df[self.df["gender_id"].isna()]["gender"].unique()
            raise ValueError(f"Bilinmeyen gender label(lar): {missing}")

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        row = self.df.iloc[idx]

        # --- Görsel ---
        img_path = row["img_path"]
        image = Image.open(img_path).convert("RGB")
        if self.image_transform is not None:
            image = self.image_transform(image)

        # --- Metin ---
        text = row["text_en"] if self.use_english else row["text_tr"]
        if not isinstance(text, str):
            text = "" if pd.isna(text) else str(text)

        encoding = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=self.max_length,
            return_tensors="pt",
        )
        input_ids = encoding["input_ids"].squeeze(0)
        attention_mask = encoding["attention_mask"].squeeze(0)

        # --- Label ---
        emotion_id = int(row["emotion_id"])
        gender_id = int(row["gender_id"])

        return {
            "id": row["id"],
            "image": image,  # Tensor [3, H, W]
            "input_ids": input_ids,  # Tensor [L]
            "attention_mask": attention_mask,  # Tensor [L]
            "emotion_label": torch.tensor(emotion_id, dtype=torch.long),
            "gender_label": torch.tensor(gender_id, dtype=torch.long),
            "raw_text": text,
            "emotion_str": row["emotion"],
            "gender_str": row["gender"],
        }
