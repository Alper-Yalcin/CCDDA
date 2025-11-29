import os
import argparse
from typing import Tuple, Dict

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, SubsetRandomSampler

from transformers import AutoTokenizer, get_cosine_schedule_with_warmup

from src.data.dataset import KidoMultimodalDataset
from src.data.transforms import get_image_transforms
from src.models.multimodal_effnet_bert import MultimodalEffNetBert


def parse_args():
    parser = argparse.ArgumentParser(description="Train multimodal EffNet+BERT on KIDO (Emotion + Gender)")

    parser.add_argument("--csv_path", type=str, default="Dataset/master_emotion_gender.csv")
    parser.add_argument("--bert_model", type=str, default="dbmdz/bert-base-turkish-cased")
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--warmup_steps", type=int, default=0)
    parser.add_argument("--val_ratio", type=float, default=0.15)
    parser.add_argument("--max_length", type=int, default=128)
    parser.add_argument("--output_dir", type=str, default="checkpoints")
    parser.add_argument("--device", type=str, default="cuda")

    # ---- Freeze / unfreeze ayarları ----
    # BERT için:
    #   default: freeze_bert = True  (yani donuk)
    #   --no_freeze_bert dersen: BERT de eğitilir
    parser.add_argument(
        "--freeze_bert",
        dest="freeze_bert",
        action="store_true",
        help="BERT parametrelerini dondur"
    )
    parser.add_argument(
        "--no_freeze_bert",
        dest="freeze_bert",
        action="store_false",
        help="BERT parametrelerini dondurma (eğit)"
    )

    # EfficientNet için:
    #   default: freeze_effnet = False (yani eğitilecek)
    #   --freeze_effnet dersen: EfficientNet donuk olur
    parser.add_argument(
        "--freeze_effnet",
        dest="freeze_effnet",
        action="store_true",
        help="EfficientNet parametrelerini dondur"
    )
    parser.add_argument(
        "--no_freeze_effnet",
        dest="freeze_effnet",
        action="store_false",
        help="EfficientNet parametrelerini dondurma (eğit)"
    )

    # Varsayılanları burada belirliyoruz:
    parser.set_defaults(
        freeze_bert=True,     # BERT varsayılan: donuk
        freeze_effnet=False,  # EffNet varsayılan: eğitilecek
    )

    return parser.parse_args()

def create_dataloaders(
    csv_path: str,
    tokenizer,
    batch_size: int,
    max_length: int,
    val_ratio: float = 0.15,
) -> Tuple[DataLoader, DataLoader]:
    """
    Train split'ten train/val ayırıyoruz.
    Test için ayrı scriptte DataLoader oluşturacağız.
    """
    train_tf, val_tf = get_image_transforms()

    full_train_dataset = KidoMultimodalDataset(
        csv_path=csv_path,
        split="train",
        tokenizer=tokenizer,
        image_transform=train_tf,
        max_length=max_length,
    )

    num_samples = len(full_train_dataset)
    indices = np.arange(num_samples)
    np.random.shuffle(indices)

    val_size = int(num_samples * val_ratio)
    val_indices = indices[:val_size]
    train_indices = indices[val_size:]

    train_sampler = SubsetRandomSampler(train_indices)
    val_sampler = SubsetRandomSampler(val_indices)

    train_loader = DataLoader(
        full_train_dataset,
        batch_size=batch_size,
        sampler=train_sampler,
        num_workers=4,
        pin_memory=True,
    )

    # val için aynı dataset ama val transform'ı kullanmak daha doğru,
    # o yüzden yeni bir dataset oluşturuyoruz:
    val_dataset = KidoMultimodalDataset(
        csv_path=csv_path,
        split="train",
        tokenizer=tokenizer,
        image_transform=val_tf,
        max_length=max_length,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        sampler=val_sampler,
        num_workers=4,
        pin_memory=True,
    )

    return train_loader, val_loader


def compute_accuracy(logits: torch.Tensor, targets: torch.Tensor) -> float:
    preds = torch.argmax(logits, dim=1)
    correct = (preds == targets).sum().item()
    total = targets.size(0)
    return correct / total


def train_one_epoch(
    model: nn.Module,
    train_loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    scheduler,
    device: torch.device,
    epoch: int,
) -> Dict[str, float]:
    model.train()
    ce = nn.CrossEntropyLoss()

    total_loss = 0.0
    total_emotion_acc = 0.0
    total_gender_acc = 0.0
    total_batches = 0

    for batch_idx, batch in enumerate(train_loader):
        images = batch["image"].to(device)
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        emotion_labels = batch["emotion_label"].to(device)
        gender_labels = batch["gender_label"].to(device)

        optimizer.zero_grad()

        outputs = model(
            image=images,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        logits_emotion = outputs["logits_emotion"]
        logits_gender = outputs["logits_gender"]

        loss_emotion = ce(logits_emotion, emotion_labels)
        loss_gender = ce(logits_gender, gender_labels)
        loss = loss_emotion + loss_gender

        loss.backward()
        optimizer.step()
        if scheduler is not None:
            scheduler.step()

        # metrics
        emotion_acc = compute_accuracy(logits_emotion, emotion_labels)
        gender_acc = compute_accuracy(logits_gender, gender_labels)

        total_loss += loss.item()
        total_emotion_acc += emotion_acc
        total_gender_acc += gender_acc
        total_batches += 1

        if (batch_idx + 1) % 50 == 0:
            print(
                f"Epoch [{epoch}] Step [{batch_idx+1}/{len(train_loader)}] "
                f"Loss: {loss.item():.4f} "
                f"Emotion Acc: {emotion_acc:.4f} "
                f"Gender Acc: {gender_acc:.4f}"
            )

    return {
        "loss": total_loss / total_batches,
        "emotion_acc": total_emotion_acc / total_batches,
        "gender_acc": total_gender_acc / total_batches,
    }


def validate(
    model: nn.Module,
    val_loader: DataLoader,
    device: torch.device,
) -> Dict[str, float]:
    model.eval()
    ce = nn.CrossEntropyLoss()

    total_loss = 0.0
    total_emotion_acc = 0.0
    total_gender_acc = 0.0
    total_batches = 0

    torch.set_grad_enabled(False)
    for batch in val_loader:
        images = batch["image"].to(device)
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        emotion_labels = batch["emotion_label"].to(device)
        gender_labels = batch["gender_label"].to(device)

        outputs = model(
            image=images,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        logits_emotion = outputs["logits_emotion"]
        logits_gender = outputs["logits_gender"]

        loss_emotion = ce(logits_emotion, emotion_labels)
        loss_gender = ce(logits_gender, gender_labels)
        loss = loss_emotion + loss_gender

        emotion_acc = compute_accuracy(logits_emotion, emotion_labels)
        gender_acc = compute_accuracy(logits_gender, gender_labels)

        total_loss += loss.item()
        total_emotion_acc += emotion_acc
        total_gender_acc += gender_acc
        total_batches += 1

    torch.set_grad_enabled(True)

    return {
        "loss": total_loss / total_batches,
        "emotion_acc": total_emotion_acc / total_batches,
        "gender_acc": total_gender_acc / total_batches,
    }


def main():
    args = parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(args.bert_model)

    print("Creating dataloaders...")
    train_loader, val_loader = create_dataloaders(
        csv_path=args.csv_path,
        tokenizer=tokenizer,
        batch_size=args.batch_size,
        max_length=args.max_length,
        val_ratio=args.val_ratio,
    )

    print("Initializing model...")
    model = MultimodalEffNetBert(
        bert_model_name=args.bert_model,
        freeze_bert=args.freeze_bert,
        freeze_effnet=args.freeze_effnet,
    ).to(device)

    # Parametre listesi (sadece trainable olanlar)
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    print("Trainable parameter count:", sum(p.numel() for p in trainable_params))

    optimizer = torch.optim.AdamW(
        trainable_params,
        lr=args.lr,
        weight_decay=args.weight_decay,
    )

    total_steps = args.epochs * len(train_loader)
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=args.warmup_steps,
        num_training_steps=total_steps,
    )

    best_val_loss = float("inf")
    best_checkpoint_path = os.path.join(args.output_dir, "best_multimodal.pt")

    for epoch in range(1, args.epochs + 1):
        print(f"\n=== Epoch {epoch}/{args.epochs} ===")

        train_metrics = train_one_epoch(
            model=model,
            train_loader=train_loader,
            optimizer=optimizer,
            scheduler=scheduler,
            device=device,
            epoch=epoch,
        )
        print(
            f"Train - Loss: {train_metrics['loss']:.4f}, "
            f"Emotion Acc: {train_metrics['emotion_acc']:.4f}, "
            f"Gender Acc: {train_metrics['gender_acc']:.4f}"
        )

        val_metrics = validate(
            model=model,
            val_loader=val_loader,
            device=device,
        )
        print(
            f"Val   - Loss: {val_metrics['loss']:.4f}, "
            f"Emotion Acc: {val_metrics['emotion_acc']:.4f}, "
            f"Gender Acc: {val_metrics['gender_acc']:.4f}"
        )

        # En iyi modeli kaydet
        if val_metrics["loss"] < best_val_loss:
            best_val_loss = val_metrics["loss"]
            torch.save(
                {
                    "epoch": epoch,
                    "model_state_dict": model.state_dict(),
                    "optimizer_state_dict": optimizer.state_dict(),
                    "val_metrics": val_metrics,
                    "args": vars(args),
                },
                best_checkpoint_path,
            )
            print(f"✅ Yeni en iyi model kaydedildi: {best_checkpoint_path}")

    print("\nEğitim tamamlandı.")
    print("En iyi val loss:", best_val_loss)


if __name__ == "__main__":
    main()
