import os
import torch
from torch.utils.data import DataLoader

from transformers import AutoTokenizer

from src.data.dataset import KidoMultimodalDataset
from src.data.transforms import get_image_transforms
from src.models.multimodal_effnet_bert import MultimodalEffNetBert


def compute_accuracy(logits, targets):
    preds = torch.argmax(logits, dim=1)
    correct = (preds == targets).sum().item()
    total = targets.size(0)
    return correct, total


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    checkpoint_path = os.path.join("checkpoints", "best_multimodal.pt")
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(checkpoint_path)

    print("Loading checkpoint:", checkpoint_path)
    ckpt = torch.load(checkpoint_path, map_location=device)
    ckpt_args = ckpt.get("args", {})

    bert_model_name = ckpt_args.get("bert_model", "dbmdz/bert-base-turkish-cased")
    csv_path = ckpt_args.get("csv_path", "Dataset/master_emotion_gender.csv")
    max_length = ckpt_args.get("max_length", 128)
    batch_size = ckpt_args.get("batch_size", 16)

    print("Loading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(bert_model_name)

    _, val_tf = get_image_transforms()

    print("Creating test dataset...")
    test_dataset = KidoMultimodalDataset(
        csv_path=csv_path,
        split="test",
        tokenizer=tokenizer,
        image_transform=val_tf,
        max_length=max_length,
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=4,
        pin_memory=True,
    )

    print("Initializing model...")
    model = MultimodalEffNetBert(
        bert_model_name=bert_model_name,
        freeze_bert=True,
        freeze_effnet=True,
    ).to(device)

    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    total_emotion_correct = 0
    total_gender_correct = 0
    total_samples = 0

    with torch.no_grad():
        for batch in test_loader:
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

            ce, te = compute_accuracy(logits_emotion, emotion_labels)
            cg, tg = compute_accuracy(logits_gender, gender_labels)

            total_emotion_correct += ce
            total_gender_correct += cg
            total_samples += te  # == tg

    emotion_acc = total_emotion_correct / total_samples
    gender_acc = total_gender_correct / total_samples

    print(f"Test Emotion Acc: {emotion_acc:.4f}")
    print(f"Test Gender Acc : {gender_acc:.4f}")
    print(f"Test Overall (both correct approx.): ~{(emotion_acc * gender_acc):.4f}")


if __name__ == "__main__":
    main()
