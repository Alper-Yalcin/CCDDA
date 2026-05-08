"""
SigLIPDrawingDataset: manifest.csv + (opsiyonel) features_v1.csv ile besler.

__getitem__ donusumu:
{
    "image": Tensor[3,224,224],
    "clinical_features": Tensor[18],
    "clinical_validity": Tensor[18],
    "label": int,
    "sample_id": str,
}

Eger features_csv verilmezse klinik vektor sifir doldurulur, validity 0 olur.
Bu sayede image-only baseline da ayni Dataset uzerinden egitilebilir.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

from src.features.feature_spec import FEATURE_NAMES, NUM_FEATURES


class SigLIPDrawingDataset(Dataset):
    def __init__(
        self,
        manifest_csv: str | Path,
        split: str,
        transform=None,
        features_csv: Optional[str | Path] = None,
    ) -> None:
        df = pd.read_csv(manifest_csv)
        df = df[df["split"] == split].reset_index(drop=True)
        if df.empty:
            raise ValueError(f"Manifest'te '{split}' split'i bos.")
        self.df = df
        self.transform = transform

        self.feature_lookup: Optional[pd.DataFrame] = None
        if features_csv is not None and Path(features_csv).is_file():
            feat_df = pd.read_csv(features_csv).set_index("sample_id")
            self.feature_lookup = feat_df

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int) -> dict:
        row = self.df.iloc[idx]
        sample_id = str(row["sample_id"])
        label = int(row["label_id"])

        img = Image.open(row["image_path"]).convert("RGB")
        if self.transform is not None:
            image_t = self.transform(img)
        else:
            image_t = torch.zeros(3, 224, 224)

        clinical = np.zeros(NUM_FEATURES, dtype=np.float32)
        validity = np.zeros(NUM_FEATURES, dtype=np.float32)
        if self.feature_lookup is not None and sample_id in self.feature_lookup.index:
            feat_row = self.feature_lookup.loc[sample_id]
            for i, name in enumerate(FEATURE_NAMES):
                v = feat_row.get(name)
                vflag = feat_row.get(f"{name}_valid")
                if v is not None and pd.notna(v) and vflag is not None and int(vflag) == 1:
                    clinical[i] = float(v)
                    validity[i] = 1.0

        return {
            "image": image_t,
            "clinical_features": torch.from_numpy(clinical),
            "clinical_validity": torch.from_numpy(validity),
            "label": label,
            "sample_id": sample_id,
        }
