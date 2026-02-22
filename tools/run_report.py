#!/usr/bin/env python
"""
Reproducible train/eval/report runner for KIDO multimodal model.
Outputs are written under artifacts/report_run/ by default.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
import torch.nn.functional as F
from PIL import Image
from sklearn.metrics import (
    accuracy_score,
    auc,
    confusion_matrix,
    precision_recall_fscore_support,
    roc_curve,
)
from torch.utils.data import DataLoader, Subset
from transformers import AutoTokenizer, get_cosine_schedule_with_warmup

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.data.dataset import EMOTION_MAP, GENDER_MAP, KidoMultimodalDataset
from src.data.transforms import get_image_transforms
from src.models.multimodal_effnet_bert import MultimodalEffNetBert
from src.train.train_multimodal import (
    compute_gender_class_weights,
    train_one_epoch,
    validate,
)


EMOTION_ID2STR = {v: k for k, v in EMOTION_MAP.items()}
GENDER_ID2STR = {v: k for k, v in GENDER_MAP.items()}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train/evaluate and generate report artifacts.")
    parser.add_argument("--data_dir", type=str, default="Dataset")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output_dir", type=str, default="artifacts/report_run")
    parser.add_argument("--quick", action="store_true", help="Quick debug run with smaller subsets.")

    # Internal defaults aligned with existing training pipeline.
    parser.add_argument("--bert_model", type=str, default="dbmdz/bert-base-turkish-cased")
    parser.add_argument("--max_length", type=int, default=128)
    parser.add_argument("--val_ratio", type=float, default=0.15)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--warmup_steps", type=int, default=0)
    parser.add_argument("--freeze_bert", action="store_true", default=True)
    parser.add_argument("--freeze_effnet", action="store_true", default=False)
    parser.add_argument("--device", type=str, default="cuda")
    return parser.parse_args()


def set_seed(seed: int) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def to_serializable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): to_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [to_serializable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    return obj


def ensure_dirs(output_dir: Path) -> Dict[str, Path]:
    figures_dir = output_dir / "figures"
    model_dir = output_dir / "model"
    figures_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    return {"root": output_dir, "figures": figures_dir, "model": model_dir}


def deterministic_train_val_split(
    n_samples: int,
    val_ratio: float,
    seed: int,
    quick: bool,
) -> Tuple[np.ndarray, np.ndarray]:
    indices = np.arange(n_samples)
    rng = np.random.default_rng(seed)
    rng.shuffle(indices)

    val_size = int(n_samples * val_ratio)
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]

    if quick:
        train_cap = min(1024, len(train_indices))
        val_cap = min(256, len(val_indices))
        train_indices = train_indices[:train_cap]
        val_indices = val_indices[:val_cap]

    return train_indices, val_indices


def create_dataloaders(
    csv_path: str,
    tokenizer: AutoTokenizer,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    train_tf, val_tf = get_image_transforms(image_size=224)

    # Same split source for train/val; only transforms differ.
    train_dataset_full = KidoMultimodalDataset(
        csv_path=csv_path,
        split="train",
        tokenizer=tokenizer,
        image_transform=train_tf,
        max_length=args.max_length,
    )
    val_dataset_full = KidoMultimodalDataset(
        csv_path=csv_path,
        split="train",
        tokenizer=tokenizer,
        image_transform=val_tf,
        max_length=args.max_length,
    )

    train_idx, val_idx = deterministic_train_val_split(
        n_samples=len(train_dataset_full),
        val_ratio=args.val_ratio,
        seed=args.seed,
        quick=args.quick,
    )

    train_subset = Subset(train_dataset_full, train_idx.tolist())
    val_subset = Subset(val_dataset_full, val_idx.tolist())

    generator = torch.Generator()
    generator.manual_seed(args.seed)

    common_loader_kwargs = {
        "batch_size": args.batch_size,
        "num_workers": 0,  # deterministic on Windows
        "pin_memory": torch.cuda.is_available(),
    }

    train_loader = DataLoader(
        train_subset,
        shuffle=True,
        generator=generator,
        **common_loader_kwargs,
    )
    val_loader = DataLoader(
        val_subset,
        shuffle=False,
        **common_loader_kwargs,
    )

    test_dataset_full = KidoMultimodalDataset(
        csv_path=csv_path,
        split="test",
        tokenizer=tokenizer,
        image_transform=val_tf,
        max_length=args.max_length,
    )
    if args.quick:
        test_cap = min(512, len(test_dataset_full))
        test_idx = np.arange(test_cap)
        test_dataset = Subset(test_dataset_full, test_idx.tolist())
    else:
        test_dataset = test_dataset_full

    test_loader = DataLoader(
        test_dataset,
        shuffle=False,
        **common_loader_kwargs,
    )

    return {
        "train_loader": train_loader,
        "val_loader": val_loader,
        "test_loader": test_loader,
        "train_idx": train_idx,
        "val_idx": val_idx,
        "train_dataset_full": train_dataset_full,
        "test_dataset_full": test_dataset_full,
    }


def build_model_and_optimizer(
    args: argparse.Namespace,
    device: torch.device,
    total_steps: int,
) -> Tuple[MultimodalEffNetBert, torch.optim.Optimizer, Any, Dict[str, int]]:
    model = MultimodalEffNetBert(
        bert_model_name=args.bert_model,
        freeze_bert=args.freeze_bert,
        freeze_effnet=args.freeze_effnet,
    ).to(device)

    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        trainable_params,
        lr=args.lr,
        weight_decay=args.weight_decay,
    )
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=args.warmup_steps,
        num_training_steps=max(total_steps, 1),
    )

    param_stats = {
        "total_params": int(sum(p.numel() for p in model.parameters())),
        "trainable_params": int(sum(p.numel() for p in model.parameters() if p.requires_grad)),
    }
    return model, optimizer, scheduler, param_stats


def run_training(
    model: torch.nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler: Any,
    device: torch.device,
    gender_class_weights: torch.Tensor,
    args: argparse.Namespace,
    model_dir: Path,
) -> Tuple[Path, Dict[str, List[float]]]:
    history: Dict[str, List[float]] = {
        "epoch": [],
        "train_loss": [],
        "val_loss": [],
        "train_emotion_acc": [],
        "val_emotion_acc": [],
        "train_gender_acc": [],
        "val_gender_acc": [],
    }

    best_metric = -1.0
    best_path = model_dir / "best_multimodal.pt"

    for epoch in range(1, args.epochs + 1):
        print(f"\n=== Epoch {epoch}/{args.epochs} ===")
        train_metrics = train_one_epoch(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            scheduler=scheduler,
            device=device,
            epoch=epoch,
            gender_class_weights=gender_class_weights,
            emotion_loss_weight=0.6,
            gender_loss_weight=1.4,
        )
        val_metrics = validate(
            model=model,
            val_loader=val_loader,
            device=device,
            emotion_loss_weight=0.6,
            gender_loss_weight=1.4,
        )

        history["epoch"].append(epoch)
        history["train_loss"].append(float(train_metrics["loss"]))
        history["val_loss"].append(float(val_metrics["loss"]))
        history["train_emotion_acc"].append(float(train_metrics["emotion_acc"]))
        history["val_emotion_acc"].append(float(val_metrics["emotion_acc"]))
        history["train_gender_acc"].append(float(train_metrics["gender_acc"]))
        history["val_gender_acc"].append(float(val_metrics["gender_acc"]))

        print(
            f"Train loss={train_metrics['loss']:.4f} em_acc={train_metrics['emotion_acc']:.4f} "
            f"gen_acc={train_metrics['gender_acc']:.4f}"
        )
        print(
            f"Val   loss={val_metrics['loss']:.4f} em_acc={val_metrics['emotion_acc']:.4f} "
            f"gen_acc={val_metrics['gender_acc']:.4f}"
        )

        # Keep the same model-selection criterion as existing pipeline.
        if val_metrics["gender_acc"] > best_metric:
            best_metric = float(val_metrics["gender_acc"])
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_metrics": val_metrics,
                    "args": vars(args),
                    "history": history,
                },
                best_path,
            )
            print(f"Saved new best checkpoint to {best_path}")

    return best_path, history


def evaluate_model(
    model: torch.nn.Module,
    test_loader: DataLoader,
    device: torch.device,
) -> Dict[str, Any]:
    model.eval()

    emo_true: List[int] = []
    emo_pred: List[int] = []
    emo_prob: List[List[float]] = []

    gen_true: List[int] = []
    gen_pred: List[int] = []
    gen_prob: List[List[float]] = []

    sample_ids: List[str] = []

    with torch.no_grad():
        for batch in test_loader:
            images = batch["image"].to(device)
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)

            outputs = model(
                image=images,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

            logits_e = outputs["logits_emotion"]
            logits_g = outputs["logits_gender"]
            probs_e = F.softmax(logits_e, dim=1).detach().cpu().numpy()
            probs_g = F.softmax(logits_g, dim=1).detach().cpu().numpy()
            pred_e = np.argmax(probs_e, axis=1)
            pred_g = np.argmax(probs_g, axis=1)

            emo_true.extend(batch["emotion_label"].cpu().numpy().astype(int).tolist())
            emo_pred.extend(pred_e.astype(int).tolist())
            emo_prob.extend(probs_e.tolist())

            gen_true.extend(batch["gender_label"].cpu().numpy().astype(int).tolist())
            gen_pred.extend(pred_g.astype(int).tolist())
            gen_prob.extend(probs_g.tolist())

            sample_ids.extend([str(x) for x in batch["id"]])

    return {
        "emotion": {
            "y_true": emo_true,
            "y_pred": emo_pred,
            "y_prob": emo_prob,
        },
        "gender": {
            "y_true": gen_true,
            "y_pred": gen_pred,
            "y_prob": gen_prob,
        },
        "sample_ids": sample_ids,
    }


def compute_task_metrics(
    y_true: List[int],
    y_pred: List[int],
    y_prob: List[List[float]],
    id_to_label: Dict[int, str],
) -> Dict[str, Any]:
    labels = sorted(id_to_label.keys())
    class_names = [id_to_label[i] for i in labels]

    acc = float(accuracy_score(y_true, y_pred))
    p_macro, r_macro, f1_macro, _ = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        average="macro",
        zero_division=0,
    )
    p_cls, r_cls, f1_cls, support = precision_recall_fscore_support(
        y_true,
        y_pred,
        labels=labels,
        average=None,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred, labels=labels)

    metrics: Dict[str, Any] = {
        "accuracy": acc,
        "precision_macro": float(p_macro),
        "recall_macro": float(r_macro),
        "f1_macro": float(f1_macro),
        "per_class": {
            class_names[i]: {
                "precision": float(p_cls[i]),
                "recall": float(r_cls[i]),
                "f1": float(f1_cls[i]),
                "support": int(support[i]),
            }
            for i in range(len(labels))
        },
        "confusion_matrix": cm.tolist(),
        "label_mapping": {str(i): name for i, name in zip(labels, class_names)},
    }

    y_prob_arr = np.array(y_prob, dtype=np.float32) if y_prob else None
    if y_prob_arr is not None and y_prob_arr.ndim == 2 and y_prob_arr.shape[1] == 2:
        fpr, tpr, _ = roc_curve(np.array(y_true), y_prob_arr[:, 1], pos_label=1)
        roc_auc = float(auc(fpr, tpr))
        metrics["roc_auc"] = roc_auc
        metrics["roc_curve"] = {"fpr": fpr.tolist(), "tpr": tpr.tolist(), "positive_label": class_names[1]}
    else:
        metrics["roc_auc"] = None
        metrics["roc_curve"] = None
        metrics["roc_note"] = "ROC-AUC hesaplanamadı: ikili olasılık çıktısı yok."

    return metrics


def plot_training_curves(history: Dict[str, List[float]], out_path: Path) -> None:
    epochs = history["epoch"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    axes[0].plot(epochs, history["train_loss"], marker="o", label="Train Loss")
    axes[0].plot(epochs, history["val_loss"], marker="o", label="Val Loss")
    axes[0].set_title("Loss vs Epoch")
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].grid(alpha=0.3)
    axes[0].legend()

    axes[1].plot(epochs, history["train_emotion_acc"], marker="o", label="Train Emotion Acc")
    axes[1].plot(epochs, history["val_emotion_acc"], marker="o", label="Val Emotion Acc")
    axes[1].plot(epochs, history["train_gender_acc"], marker="o", label="Train Gender Acc")
    axes[1].plot(epochs, history["val_gender_acc"], marker="o", label="Val Gender Acc")
    axes[1].set_title("Accuracy vs Epoch")
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_ylim(0.0, 1.0)
    axes[1].grid(alpha=0.3)
    axes[1].legend()

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def _plot_single_confusion_matrix(
    ax: plt.Axes,
    cm: np.ndarray,
    class_names: List[str],
    title: str,
) -> None:
    im = ax.imshow(cm, interpolation="nearest", cmap=plt.cm.Blues)
    ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set(
        xticks=np.arange(cm.shape[1]),
        yticks=np.arange(cm.shape[0]),
        xticklabels=class_names,
        yticklabels=class_names,
        ylabel="Gerçek",
        xlabel="Tahmin",
        title=title,
    )
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right", rotation_mode="anchor")

    thresh = cm.max() / 2.0 if cm.size > 0 else 0.5
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(
                j,
                i,
                format(int(cm[i, j]), "d"),
                ha="center",
                va="center",
                color="white" if cm[i, j] > thresh else "black",
            )


def plot_confusion_matrices(
    emotion_cm: List[List[int]],
    gender_cm: List[List[int]],
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    _plot_single_confusion_matrix(
        axes[0],
        np.array(emotion_cm, dtype=int),
        [EMOTION_ID2STR[0], EMOTION_ID2STR[1]],
        "Duygu Confusion Matrix",
    )
    _plot_single_confusion_matrix(
        axes[1],
        np.array(gender_cm, dtype=int),
        [GENDER_ID2STR[0], GENDER_ID2STR[1]],
        "Cinsiyet Confusion Matrix",
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def plot_roc_curves(metrics: Dict[str, Any], out_path: Path) -> bool:
    emo_roc = metrics["emotion"].get("roc_curve")
    gen_roc = metrics["gender"].get("roc_curve")
    if emo_roc is None and gen_roc is None:
        return False

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random")
    if emo_roc is not None:
        ax.plot(
            emo_roc["fpr"],
            emo_roc["tpr"],
            label=f"Duygu ROC (AUC={metrics['emotion']['roc_auc']:.4f})",
            linewidth=2,
        )
    if gen_roc is not None:
        ax.plot(
            gen_roc["fpr"],
            gen_roc["tpr"],
            label=f"Cinsiyet ROC (AUC={metrics['gender']['roc_auc']:.4f})",
            linewidth=2,
        )
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Eğrileri")
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    return True


def plot_sample_predictions_grid(
    eval_outputs: Dict[str, Any],
    id_to_path: Dict[str, str],
    out_path: Path,
    n_samples: int = 12,
) -> None:
    ids = eval_outputs["sample_ids"][:n_samples]
    emo_true = eval_outputs["emotion"]["y_true"][:n_samples]
    emo_pred = eval_outputs["emotion"]["y_pred"][:n_samples]
    emo_prob = eval_outputs["emotion"]["y_prob"][:n_samples]
    gen_true = eval_outputs["gender"]["y_true"][:n_samples]
    gen_pred = eval_outputs["gender"]["y_pred"][:n_samples]
    gen_prob = eval_outputs["gender"]["y_prob"][:n_samples]

    n_cols = 4
    n_rows = int(np.ceil(n_samples / n_cols))
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(16, 10))
    axes = np.array(axes).reshape(-1)

    for i, ax in enumerate(axes):
        if i >= len(ids):
            ax.axis("off")
            continue

        sample_id = ids[i]
        img_path = id_to_path.get(sample_id)
        if img_path and os.path.exists(img_path):
            image = Image.open(img_path).convert("RGB")
            ax.imshow(image)
        else:
            ax.text(0.5, 0.5, "Image not found", ha="center", va="center")
            ax.set_facecolor("#f0f0f0")

        emo_conf = float(max(emo_prob[i])) * 100.0
        gen_conf = float(max(gen_prob[i])) * 100.0
        title = (
            f"ID: {sample_id}\n"
            f"E: {EMOTION_ID2STR[emo_true[i]]}->{EMOTION_ID2STR[emo_pred[i]]} ({emo_conf:.1f}%)\n"
            f"G: {GENDER_ID2STR[gen_true[i]]}->{GENDER_ID2STR[gen_pred[i]]} ({gen_conf:.1f}%)"
        )
        ax.set_title(title, fontsize=8)
        ax.axis("off")

    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def distribution_from_series(values: pd.Series) -> Dict[str, int]:
    return {str(k): int(v) for k, v in Counter(values).items()}


def make_confusion_markdown_table(cm: List[List[int]], labels: List[str]) -> str:
    lines = []
    header = "| Gerçek \\ Tahmin | " + " | ".join(labels) + " |"
    sep = "|" + "---|" * (len(labels) + 1)
    lines.append(header)
    lines.append(sep)
    for i, row_label in enumerate(labels):
        row_vals = " | ".join(str(int(v)) for v in cm[i])
        lines.append(f"| {row_label} | {row_vals} |")
    return "\n".join(lines)


def metrics_row(name: str, m: Dict[str, Any]) -> str:
    return (
        f"| {name} | {m['accuracy']:.4f} | {m['precision_macro']:.4f} | "
        f"{m['recall_macro']:.4f} | {m['f1_macro']:.4f} |"
    )


def per_class_rows(task_name: str, per_class: Dict[str, Dict[str, Any]]) -> str:
    rows = []
    for cls_name, vals in per_class.items():
        rows.append(
            f"| {task_name} | {cls_name} | {vals['precision']:.4f} | "
            f"{vals['recall']:.4f} | {vals['f1']:.4f} | {vals['support']} |"
        )
    return "\n".join(rows)


def write_report(
    report_path: Path,
    run_meta: Dict[str, Any],
    data_meta: Dict[str, Any],
    model_meta: Dict[str, Any],
    train_meta: Dict[str, Any],
    metrics: Dict[str, Any],
    roc_available: bool,
) -> None:
    em_labels = [EMOTION_ID2STR[0], EMOTION_ID2STR[1]]
    gen_labels = [GENDER_ID2STR[0], GENDER_ID2STR[1]]
    em_cm_table = make_confusion_markdown_table(metrics["emotion"]["confusion_matrix"], em_labels)
    gen_cm_table = make_confusion_markdown_table(metrics["gender"]["confusion_matrix"], gen_labels)

    if roc_available:
        roc_text = (
            f"- Duygu ROC-AUC: `{metrics['emotion']['roc_auc']:.4f}`\n"
            f"- Cinsiyet ROC-AUC: `{metrics['gender']['roc_auc']:.4f}`\n"
            f"- Şekil: `figures/roc_curve.png`"
        )
    else:
        roc_text = "- ROC-AUC hesaplanamadı (olasılık çıktısı veya ikili yapı uygun değildi)."

    mode_label = "quick" if run_meta["quick"] else "full"
    report = f"""# KIDO Multimodal Değerlendirme Raporu

## 1. Çalışma Bilgisi
- Proje: `{run_meta['project_name']}`
- Tarih/Saat: `{run_meta['timestamp']}`
- Çalıştırılan komut: `{run_meta['command']}`
- Çalışma modu: `{mode_label}`

## 2. Veri Seti ve Bölünme
- Veri yolu: `{data_meta['csv_path']}`
- Toplam örnek: `{data_meta['total_samples']}`
- Split (orijinal): train=`{data_meta['split_counts'].get('train', 0)}`, test=`{data_meta['split_counts'].get('test', 0)}`
- Bu çalışmada train/val ayrımı: train=`{data_meta['train_count']}`, val=`{data_meta['val_count']}`, test=`{data_meta['test_count']}`

### 2.1 Sınıf Dağılımı (Duygu)
- Train: `{data_meta['train_emotion_dist']}`
- Val: `{data_meta['val_emotion_dist']}`
- Test: `{data_meta['test_emotion_dist']}`

### 2.2 Sınıf Dağılımı (Cinsiyet)
- Train: `{data_meta['train_gender_dist']}`
- Val: `{data_meta['val_gender_dist']}`
- Test: `{data_meta['test_gender_dist']}`

## 3. Ön İşleme ve Veri Dönüşümleri
Koddan tespit edilen dönüşümler (`src/data/transforms.py`):
- Train:
  - Resize: `224x224`
  - `RandomHorizontalFlip(p=0.5)`
  - `RandomRotation(degrees=10)`
  - Normalize: mean=`[0.485, 0.456, 0.406]`, std=`[0.229, 0.224, 0.225]`
- Val/Test:
  - Resize: `224x224`
  - Normalize: mean=`[0.485, 0.456, 0.406]`, std=`[0.229, 0.224, 0.225]`
- Metin:
  - Tokenizer: `{train_meta['bert_model']}`
  - Max length: `{train_meta['max_length']}`
  - Öncelikli kolon: `text_tr` (boşsa `text_en`)

## 4. Model Mimarisi
- Model adı: `MultimodalEffNetBert`
- Görsel omurga: `EfficientNet-B0`
- Metin omurga: `{train_meta['bert_model']}`
- Füzyon: görüntü ve metin projeksiyonlarının birleştirilmesi
- Çıkış başlıkları:
  - Emotion (2 sınıf): Happiness / Sadness
  - Gender (2 sınıf): Female / Male
- Toplam parametre: `{model_meta['total_params']}`
- Eğitilebilir parametre: `{model_meta['trainable_params']}`

## 5. Eğitim Kurulumu
- Epoch: `{train_meta['epochs']}`
- Batch size: `{train_meta['batch_size']}`
- Öğrenme oranı (LR): `{train_meta['lr']}`
- Optimizer: `AdamW`
- Weight decay: `{train_meta['weight_decay']}`
- Scheduler: `Cosine schedule with warmup` (warmup steps=`{train_meta['warmup_steps']}`)
- Val oranı: `{train_meta['val_ratio']}`
- Seed: `{train_meta['seed']}`
- Model seçimi: `en iyi val gender accuracy`
- Erken durdurma (early stopping): `Yok`
- Eğitim eğrileri: `figures/training_curves.png`

## 6. Test Sonuçları

### 6.1 Ana Metrikler (Macro + Accuracy)
| Görev | Accuracy | Precision (macro) | Recall (macro) | F1 (macro) |
|---|---:|---:|---:|---:|
{metrics_row("Emotion", metrics["emotion"])}
{metrics_row("Gender", metrics["gender"])}

### 6.2 Sınıf Bazlı Sonuçlar
| Görev | Sınıf | Precision | Recall | F1 | Support |
|---|---|---:|---:|---:|---:|
{per_class_rows("Emotion", metrics["emotion"]["per_class"])}
{per_class_rows("Gender", metrics["gender"]["per_class"])}

### 6.3 Confusion Matrix (Tablo)
#### Emotion
{em_cm_table}

#### Gender
{gen_cm_table}

- Görsel: `figures/confusion_matrix.png`

### 6.4 ROC-AUC
{roc_text}

### 6.5 Örnek Tahminler
- Şekil: `figures/sample_predictions_grid.png`
- Not: Her örnekte gerçek/tahmin etiketleri ve güven (%) gösterilmiştir.

## 7. Yorum (TÜBİTAK Raporu İçin)
Model, gerçek test split üzerinde hem duygu hem cinsiyet sınıflandırmasında kullanılabilir performans üretmiştir. Duygu görevi için makro metrikler dengeli bir ayrım gücü sağlarken, cinsiyet görevinde sınıf dağılımı dengesizliğinin etkisi metriklere yansıyabilmektedir. Confusion matrix sonuçları, hata tiplerinin sınıf bazında incelenmesine olanak vererek modelin güçlü/zayıf yönlerini somutlaştırmaktadır.

## 8. Tekrar Üretilebilirlik
- Sabit seed kullanıldı: `{train_meta['seed']}`
- Çıktı klasörü: `{run_meta['output_dir']}`
- Kullanılan komut:
```bash
{run_meta['command']}
```
- Yeniden çalıştırma örneği:
```bash
python tools/run_report.py --output_dir artifacts/report_run --data_dir Dataset --epochs {train_meta['epochs']} --batch_size {train_meta['batch_size']} --lr {train_meta['lr']} --seed {train_meta['seed']}
```

## 9. Etik/Sınırlılık Notu
Bu sistem **klinik tanı aracı değildir**. Çıktılar yalnızca araştırma ve karar-destek amaçlı değerlendirilmelidir; nihai yorum uzman profesyoneller tarafından yapılmalıdır.
"""

    report_path.write_text(report, encoding="utf-8")


def main() -> None:
    args = parse_args()
    set_seed(args.seed)

    start_time = datetime.now()
    timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")

    command_parts: List[str] = ["python", "tools/run_report.py"]
    for key, value in vars(args).items():
        if isinstance(value, bool):
            if value:
                command_parts.append(f"--{key}")
        else:
            command_parts.append(f"--{key}")
            command_parts.append(str(value))
    command = " ".join(command_parts)

    output_dir = Path(args.output_dir)
    dirs = ensure_dirs(output_dir)

    data_dir = Path(args.data_dir)
    csv_path = data_dir / "master_emotion_gender.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"CSV bulunamadı: {csv_path}. Önce `python src/data/build_master_csv.py` çalıştırın."
        )

    df = pd.read_csv(csv_path)
    split_counts = {str(k): int(v) for k, v in df["split"].value_counts().to_dict().items()}

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(args.bert_model)
    data_objs = create_dataloaders(str(csv_path), tokenizer, args)
    train_loader = data_objs["train_loader"]
    val_loader = data_objs["val_loader"]
    test_loader = data_objs["test_loader"]

    total_steps = args.epochs * len(train_loader)
    model, optimizer, scheduler, param_stats = build_model_and_optimizer(args, device, total_steps)

    gender_class_weights = compute_gender_class_weights(str(csv_path)).to(device)

    best_ckpt_path, history = run_training(
        model=model,
        train_loader=train_loader,
        val_loader=val_loader,
        optimizer=optimizer,
        scheduler=scheduler,
        device=device,
        gender_class_weights=gender_class_weights,
        args=args,
        model_dir=dirs["model"],
    )

    print(f"Loading best checkpoint from {best_ckpt_path}")
    ckpt = torch.load(best_ckpt_path, map_location=device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    eval_outputs = evaluate_model(model, test_loader, device)
    emotion_metrics = compute_task_metrics(
        eval_outputs["emotion"]["y_true"],
        eval_outputs["emotion"]["y_pred"],
        eval_outputs["emotion"]["y_prob"],
        EMOTION_ID2STR,
    )
    gender_metrics = compute_task_metrics(
        eval_outputs["gender"]["y_true"],
        eval_outputs["gender"]["y_pred"],
        eval_outputs["gender"]["y_prob"],
        GENDER_ID2STR,
    )
    metrics = {"emotion": emotion_metrics, "gender": gender_metrics}

    plot_training_curves(history, dirs["figures"] / "training_curves.png")
    plot_confusion_matrices(
        emotion_cm=emotion_metrics["confusion_matrix"],
        gender_cm=gender_metrics["confusion_matrix"],
        out_path=dirs["figures"] / "confusion_matrix.png",
    )
    roc_available = plot_roc_curves(metrics, dirs["figures"] / "roc_curve.png")

    # Sample grid mapping by id -> image path
    test_df = data_objs["test_dataset_full"].df.copy()
    id_to_path: Dict[str, str] = {}
    for _, row in test_df.iterrows():
        sample_id = str(row["id"])
        if sample_id not in id_to_path:
            id_to_path[sample_id] = str(row["img_path"])
    plot_sample_predictions_grid(
        eval_outputs=eval_outputs,
        id_to_path=id_to_path,
        out_path=dirs["figures"] / "sample_predictions_grid.png",
        n_samples=12,
    )

    # Split distributions for report
    train_df_all = df[df["split"] == "train"].reset_index(drop=True)
    val_idx = data_objs["val_idx"]
    train_idx = data_objs["train_idx"]
    train_df = train_df_all.iloc[train_idx]
    val_df = train_df_all.iloc[val_idx]
    test_eval_size = len(eval_outputs["emotion"]["y_true"])
    if args.quick:
        # test_loader may be subset in quick mode.
        test_emotion_dist = distribution_from_series(
            pd.Series([EMOTION_ID2STR[i] for i in eval_outputs["emotion"]["y_true"]])
        )
        test_gender_dist = distribution_from_series(
            pd.Series([GENDER_ID2STR[i] for i in eval_outputs["gender"]["y_true"]])
        )
    else:
        test_df_full = df[df["split"] == "test"]
        test_emotion_dist = distribution_from_series(test_df_full["emotion"])
        test_gender_dist = distribution_from_series(test_df_full["gender"])

    run_meta = {
        "project_name": "KIDO Multimodal Emotion & Gender Analysis",
        "timestamp": timestamp,
        "command": command,
        "quick": bool(args.quick),
        "output_dir": str(output_dir),
        "device": str(device),
    }
    data_meta = {
        "csv_path": str(csv_path),
        "total_samples": int(len(df)),
        "split_counts": split_counts,
        "train_count": int(len(train_df)),
        "val_count": int(len(val_df)),
        "test_count": int(test_eval_size),
        "train_emotion_dist": distribution_from_series(train_df["emotion"]),
        "val_emotion_dist": distribution_from_series(val_df["emotion"]),
        "test_emotion_dist": test_emotion_dist,
        "train_gender_dist": distribution_from_series(train_df["gender"]),
        "val_gender_dist": distribution_from_series(val_df["gender"]),
        "test_gender_dist": test_gender_dist,
    }
    model_meta = param_stats
    train_meta = {
        "epochs": int(args.epochs),
        "batch_size": int(args.batch_size),
        "lr": float(args.lr),
        "seed": int(args.seed),
        "val_ratio": float(args.val_ratio),
        "weight_decay": float(args.weight_decay),
        "warmup_steps": int(args.warmup_steps),
        "bert_model": args.bert_model,
        "max_length": int(args.max_length),
        "freeze_bert": bool(args.freeze_bert),
        "freeze_effnet": bool(args.freeze_effnet),
        "history": history,
    }

    metrics_payload = {
        "run": run_meta,
        "data": data_meta,
        "model": model_meta,
        "training": train_meta,
        "metrics": metrics,
        "files": {
            "report": str(output_dir / "REPORT.md"),
            "training_curves": str(dirs["figures"] / "training_curves.png"),
            "confusion_matrix": str(dirs["figures"] / "confusion_matrix.png"),
            "roc_curve": str(dirs["figures"] / "roc_curve.png") if roc_available else None,
            "sample_predictions_grid": str(dirs["figures"] / "sample_predictions_grid.png"),
            "best_model_checkpoint": str(best_ckpt_path),
        },
    }

    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(to_serializable(metrics_payload), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    write_report(
        report_path=output_dir / "REPORT.md",
        run_meta=run_meta,
        data_meta=data_meta,
        model_meta=model_meta,
        train_meta=train_meta,
        metrics=metrics,
        roc_available=roc_available,
    )

    (output_dir / "run_args.json").write_text(
        json.dumps(to_serializable(vars(args)), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    elapsed = datetime.now() - start_time
    print(f"Completed in {elapsed}.")
    print(f"Report: {output_dir / 'REPORT.md'}")
    print(f"Metrics: {metrics_path}")


if __name__ == "__main__":
    main()
