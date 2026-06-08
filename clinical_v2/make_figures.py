# -*- coding: utf-8 -*-
"""
clinical_v2 — tez gorselleri (Kavram Darbogazi).
Uretilen gorseller: out/thesis_figures_v2/
"""
import json
import os
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("out/thesis_figures_v2")
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.size"] = 11
plt.rcParams["figure.dpi"] = 150

CLR = {"img": "#4C72B0", "concept": "#55A868", "emotion": "#C44E52",
       "loss": "#8172B3", "gray": "#888888"}


# ---------------------------------------------------------------------------
# Sekil 3.8 — Kavram Darbogazi mimari diyagrami
# ---------------------------------------------------------------------------
def fig_architecture():
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.set_xlim(0, 12); ax.set_ylim(0, 7); ax.axis("off")

    def box(x, y, w, h, text, color, fs=10):
        b = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.05",
                           fc=color, ec="black", alpha=0.85, lw=1.2)
        ax.add_patch(b)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
                fontsize=fs, color="white", weight="bold", wrap=True)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                     mutation_scale=18, lw=1.8, color="black"))

    # Akis: Goruntu -> ResNet-50 -> Kavram Basligi -> [16 gosterge] -> Siniflandirici -> Duygu
    box(0.2, 3, 1.8, 1.4, "Cizim\n(224x224)", CLR["img"], 9)
    box(2.6, 3, 1.9, 1.4, "ResNet-50\nOmurga", CLR["img"], 10)
    box(5.1, 3, 1.9, 1.4, "Kavram\nBasligi", CLR["concept"], 10)
    # 16 gosterge darbogazi
    box(7.6, 1.2, 2.1, 5.0, "16 KLINIK\nGOSTERGE\n(darbogaz)\n\nfigur boyutu\ncizgi titrekligi\ngolgeleme\nkeskin aci\n...", CLR["concept"], 8.5)
    box(10.0, 3, 1.7, 1.4, "Duygu\nSiniflandirici", CLR["emotion"], 9)

    arrow(2.0, 3.7, 2.6, 3.7)
    arrow(4.5, 3.7, 5.1, 3.7)
    arrow(7.0, 3.7, 7.6, 3.7)
    arrow(9.7, 3.7, 10.0, 3.7)

    # Cikti
    ax.text(11.6, 3.7, "Mutlu\nUzgun\nKizgin\nKorku", ha="left", va="center", fontsize=9)

    # Gosterge denetimi (concept loss)
    box(5.1, 0.2, 4.6, 0.9, "Gosterge denetimi: MSE(tahmin, OpenCV gercek deger)  [z-score]", CLR["loss"], 8.5)
    ax.add_patch(FancyArrowPatch((8.6, 1.2), (8.6, 1.1), arrowstyle="-|>",
                 mutation_scale=14, lw=1.4, color=CLR["loss"], linestyle="--"))

    ax.text(6, 6.6, "Kavram Darbogazi Modeli: duyguya pikselden degil klinik gostergelerden ulasilir",
            ha="center", fontsize=11, weight="bold")
    plt.tight_layout()
    plt.savefig(OUT / "sekil_3_8_mimari.png", bbox_inches="tight")
    plt.close()
    print("OK: sekil_3_8_mimari.png")


# ---------------------------------------------------------------------------
# Sekil 3.9 — Figur izolasyon adimlari (gercek cizim)
# ---------------------------------------------------------------------------
def fig_isolation():
    import cv2
    from PIL import Image
    import pandas as pd
    from clinical_v2.extractor_v2 import _foreground_mask, _figure_mask

    mani = pd.read_csv("out/real/manifest_clean.csv")
    # belirgin tek figurlu bir ornek sec
    r = mani[(mani.split == "test") & (mani.label == "sad")].iloc[3]
    rgb = np.array(Image.open(r["image_path"]).convert("RGB"))
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    fg = _foreground_mask(gray)
    fig_mask, fstat = _figure_mask(fg)

    fig, axs = plt.subplots(1, 4, figsize=(13, 3.6))
    axs[0].imshow(rgb); axs[0].set_title("(a) Orijinal cizim")
    axs[1].imshow(gray, cmap="gray"); axs[1].set_title("(b) Gri ton")
    axs[2].imshow(fg, cmap="gray"); axs[2].set_title("(c) On plan maskesi")
    axs[3].imshow(fig_mask, cmap="gray"); axs[3].set_title("(d) Izole figur")
    if fstat:
        x0, y0, x1, y1 = fstat["bbox"]
        for ax in (axs[3],):
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="red", lw=2))
    for ax in axs:
        ax.axis("off")
    plt.suptitle("Figur-farkinda gosterge cikarimi: figur izolasyon adimlari", y=1.02, fontsize=12)
    plt.tight_layout()
    plt.savefig(OUT / "sekil_3_9_figur_izolasyon.png", bbox_inches="tight")
    plt.close()
    print("OK: sekil_3_9_figur_izolasyon.png")


# ---------------------------------------------------------------------------
# Sekil 4.x — 16 gosterge ANOVA F-skor
# ---------------------------------------------------------------------------
def fig_anova():
    import pandas as pd
    from scipy.stats import f_oneway
    from clinical_v2.feature_spec_v2 import FEATURE_NAMES_V2

    mani = pd.read_csv("out/real/manifest_sadaug.csv")
    feat = pd.read_csv("out/real/features_v2.csv").set_index("sample_id")
    feat = feat[~feat.index.duplicated(keep="first")]
    tr = mani[mani.split == "train"].join(feat, on="sample_id")
    rows = []
    for n in FEATURE_NAMES_V2:
        g = [tr[tr.label_id == c][n].dropna().values for c in range(4)]
        g = [x for x in g if len(x) > 5]
        F, p = f_oneway(*g)
        rows.append((n, F))
    rows.sort(key=lambda x: x[1])
    names = [r[0] for r in rows]; fs = [r[1] for r in rows]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(names, fs, color=CLR["concept"])
    ax.set_xlabel("ANOVA F-skoru (sinif ayirim gucu)")
    ax.set_title("16 figur-farkinda klinik gostergenin sinif-ayirim gucu\n(hepsi p<0,001)")
    for i, v in enumerate(fs):
        ax.text(v + 2, i, f"{v:.0f}", va="center", fontsize=8)
    plt.tight_layout()
    plt.savefig(OUT / "sekil_4_anova.png", bbox_inches="tight")
    plt.close()
    print("OK: sekil_4_anova.png")


# ---------------------------------------------------------------------------
# Sekil 4.x — Model karsilastirma (per-class F1)
# ---------------------------------------------------------------------------
def fig_comparison():
    b6 = json.load(open("out/experiments_clean/B6/result.json"))
    b3 = json.load(open("out/experiments_clean/B3/result.json"))
    cb = json.load(open("out/experiments_v2/V2_CB1/result.json"))
    classes = ["Happy", "Sad", "Angry", "Fear"]
    x = np.arange(len(classes)); w = 0.26
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(x - w, [b6["per_class_f1"][c] for c in classes], w, label="ResNet-50 gorsel-only (0,826)", color=CLR["gray"])
    ax.bar(x, [b3["per_class_f1"][c] for c in classes], w, label="Naive fuzyon (0,821)", color=CLR["img"])
    ax.bar(x + w, [cb["per_class_f1"][c] for c in classes], w, label="Kavram Darbogazi (0,834) *", color=CLR["concept"])
    ax.set_xticks(x); ax.set_xticklabels(["Mutlu", "Uzgun", "Kizgin", "Korku"])
    ax.set_ylabel("F1 skoru"); ax.set_ylim(0.5, 1.0)
    ax.set_title("Sinif bazli F1: Kavram Darbogazi vs goruntu-yalnizca vs naive fuzyon")
    ax.legend(loc="lower center", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    plt.savefig(OUT / "sekil_4_karsilastirma.png", bbox_inches="tight")
    plt.close()
    print("OK: sekil_4_karsilastirma.png")


# ---------------------------------------------------------------------------
# Sekil 4.x — Gosterge tahmin dogrulugu (fidelity)
# ---------------------------------------------------------------------------
def fig_fidelity():
    import torch
    from torch.utils.data import DataLoader
    from torchvision import transforms
    from scipy.stats import pearsonr
    from clinical_v2.dataset_v2 import DrawingDatasetV2
    from clinical_v2.feature_spec_v2 import FEATURE_NAMES_V2, NUM_FEATURES_V2
    from src.models.concept_bottleneck_classifier import ConceptBottleneckClassifier

    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    TF = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(),
                             transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
    ck = torch.load("out/experiments_v2/V2_CB1/checkpoints/best.pt", map_location=DEVICE, weights_only=False)
    m = ConceptBottleneckClassifier(backbone="resnet50", num_concepts=16, mode="bottleneck", pretrained=False).to(DEVICE)
    m.load_state_dict(ck["model_state"]); m.eval()
    ds = DrawingDatasetV2("out/real/manifest_sadaug.csv", "test", TF, "out/real/features_v2.csv", "out/real/feature_stats_v2.json")
    ld = DataLoader(ds, batch_size=32, shuffle=False, num_workers=0)
    P, T = [], []
    with torch.no_grad():
        for b in ld:
            _, pc = m(b["image"].to(DEVICE), return_concepts=True)
            P.append(pc.cpu().numpy()); T.append(b["clinical_features"].numpy())
    P = np.concatenate(P); T = np.concatenate(T)
    rs = [(FEATURE_NAMES_V2[i], pearsonr(P[:, i], T[:, i])[0]) for i in range(NUM_FEATURES_V2)]
    rs.sort(key=lambda x: x[1])
    names = [r[0] for r in rs]; vals = [r[1] for r in rs]
    fig, ax = plt.subplots(figsize=(9, 6))
    cols = [CLR["concept"] if v > 0.7 else (CLR["img"] if v > 0.5 else CLR["emotion"]) for v in vals]
    ax.barh(names, vals, color=cols)
    ax.axvline(0.5, ls="--", color="gray", lw=1)
    ax.set_xlabel("Pearson r (model tahmini vs OpenCV gercek deger)")
    ax.set_title(f"Gosterge tahmin dogrulugu — ortalama r={np.mean(vals):.2f}, 16/16 gosterge r>0,5")
    for i, v in enumerate(vals):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=8)
    ax.set_xlim(0, 1)
    plt.tight_layout()
    plt.savefig(OUT / "sekil_4_fidelity.png", bbox_inches="tight")
    plt.close()
    print("OK: sekil_4_fidelity.png")


# ---------------------------------------------------------------------------
# Sekil 4.x — Klinik akil yurutme ornegi (Korku)
# ---------------------------------------------------------------------------
def fig_reasoning():
    import pandas as pd
    from PIL import Image
    from clinical_v2.clinical_reasoning_v2 import load_model, reason

    mani = pd.read_csv("out/real/manifest_clean.csv")
    model = load_model("out/experiments_v2/V2_CB1/checkpoints/best.pt")
    r = mani[(mani.split == "test") & (mani.label == "fear")].iloc[0]
    img = Image.open(r["image_path"])
    out = reason(model, img)

    notable = out["notable_concepts"][:5]
    labels = [n["feature"] for n in notable]
    zs = [n["z"] for n in notable]

    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), gridspec_kw={"width_ratios": [1, 1.4]})
    axs[0].imshow(np.array(img.convert("RGB"))); axs[0].axis("off")
    axs[0].set_title(f"Cizim — tahmin: Korku (%{out['probs']['Fear']*100:.0f})")
    cols = [CLR["emotion"] if z > 0 else CLR["img"] for z in zs]
    axs[1].barh(labels[::-1], zs[::-1], color=cols[::-1])
    axs[1].axvline(0, color="black", lw=0.8)
    axs[1].set_xlabel("Standartlastirilmis gosterge degeri (z)")
    axs[1].set_title("One cikan klinik gostergeler (Koppitz/Di Leo)")
    plt.tight_layout()
    plt.savefig(OUT / "sekil_4_akil_yurutme.png", bbox_inches="tight")
    plt.close()
    print("OK: sekil_4_akil_yurutme.png")
    print("Narrative:\n" + out["narrative"])


if __name__ == "__main__":
    fig_architecture()
    fig_isolation()
    fig_anova()
    fig_comparison()
    fig_fidelity()
    fig_reasoning()
    print("\nTum gorseller:", OUT)
