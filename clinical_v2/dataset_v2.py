"""
clinical_v2 — v2 gostergeleri yukleyen dataset (genel feature_names destekli).

Mevcut src.data.dataset'i bozmadan, v2 gosterge isimleriyle calisir.
Z-score standartlastirma destekli.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

from clinical_v2.feature_spec_v2 import FEATURE_NAMES_V2


class DrawingDatasetV2(Dataset):
    def __init__(self, manifest_csv, split, transform=None,
                 features_csv=None, feature_stats=None,
                 feature_names=None):
        self.names = feature_names or FEATURE_NAMES_V2
        self.nfeat = len(self.names)
        df = pd.read_csv(manifest_csv)
        df = df[df["split"] == split].reset_index(drop=True)
        if df.empty:
            raise ValueError(f"'{split}' bos.")
        self.df = df
        self.transform = transform

        self.flook = None
        if features_csv is not None and Path(features_csv).is_file():
            f = pd.read_csv(features_csv).set_index("sample_id")
            self.flook = f[~f.index.duplicated(keep="first")]

        self.mean = self.std = None
        if feature_stats is not None:
            if isinstance(feature_stats, (str, Path)):
                feature_stats = json.load(open(feature_stats, encoding="utf-8"))
            self.mean = np.array([feature_stats[n]["mean"] for n in self.names], dtype=np.float32)
            self.std = np.array([feature_stats[n]["std"] for n in self.names], dtype=np.float32)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        sid = str(row["sample_id"])
        label = int(row["label_id"])
        img = Image.open(row["image_path"]).convert("RGB")
        image_t = self.transform(img) if self.transform else torch.zeros(3, 224, 224)

        clin = np.zeros(self.nfeat, dtype=np.float32)
        val = np.zeros(self.nfeat, dtype=np.float32)
        if self.flook is not None and sid in self.flook.index:
            fr = self.flook.loc[sid]
            for i, n in enumerate(self.names):
                v = fr.get(n)
                vf = fr.get(f"{n}_valid")
                if v is not None and pd.notna(v) and vf is not None and int(vf) == 1:
                    clin[i] = float(v)
                    val[i] = 1.0
        if self.mean is not None:
            z = (clin - self.mean) / self.std
            clin = np.where(val > 0, z, 0.0).astype(np.float32)

        return {"image": image_t,
                "clinical_features": torch.from_numpy(clin),
                "clinical_validity": torch.from_numpy(val),
                "label": label, "sample_id": sid}
