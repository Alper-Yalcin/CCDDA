import os
import argparse
import cv2
import numpy as np
import torch
import torch.nn.functional as F
import pandas as pd
from PIL import Image

from transformers import AutoTokenizer

from src.data.transforms import get_image_transforms
from src.models.multimodal_effnet_bert import MultimodalEffNetBert
from src.explain.gradcam import GradCAM
from src.explain.text_explain import BertTextExplainer


EMOTION_ID2STR = {0: "Happiness", 1: "Sadness"}
GENDER_ID2STR = {0: "Female", 1: "Male"}


def parse_args():
    parser = argparse.ArgumentParser(description="Predict + explain (Grad-CAM + text) for a single sample.")

    parser.add_argument("--csv_path", type=str, default="Dataset/master_emotion_gender.csv")
    parser.add_argument("--checkpoint", type=str, default="checkpoints/best_multimodal.pt")

    # Örneği seçmek için:
    parser.add_argument("--id", type=str, default=None, help="Sample ID (ör: 207-6C-543-M-S)")
    parser.add_argument("--idx", type=int, default=0, help="ID vermezsen, index ile seç (train/test fark etmiyor, tüm csv üzerinden).")

    parser.add_argument("--bert_model", type=str, default="dbmdz/bert-base-turkish-cased")
    parser.add_argument("--max_length", type=int, default=128)
    parser.add_argument("--device", type=str, default="cuda")

    parser.add_argument("--output_dir", type=str, default="explanations")
    # Grad-CAM için target layer adı — model yapına göre gerekirse değiştir
    parser.add_argument(
        "--target_layer",
        type=str,
        default="effnet",  # Gerekirse "effnet.features" / "effnet.extract_features" diye değiştirirsin
        help="Grad-CAM için hedef layer yolu (MultimodalEffNetBert içindeki attrib path)",
    )

    return parser.parse_args()


def load_sample_row(csv_path: str, sample_id: str | None, idx: int):
    df = pd.read_csv(csv_path)

    if sample_id is not None:
        rows = df[df["id"] == sample_id]
        if len(rows) == 0:
            raise ValueError(f"ID bulunamadı: {sample_id}")
        row = rows.iloc[0]
    else:
        if idx < 0 or idx >= len(df):
            raise ValueError(f"idx {idx} aralık dışında. Toplam satır: {len(df)}")
        row = df.iloc[idx]

    return row


def get_text_from_row(row):
    """
    master_emotion_gender.csv içinde metni tutan kolonları buradan seçiyoruz.
    Bizim durumda: text_tr (Türkçe) ve text_en (İngilizce).
    """
    # Öncelik: Türkçe metin
    if "text_tr" in row.index and isinstance(row["text_tr"], str) and row["text_tr"].strip():
        return str(row["text_tr"])

    # Eğer Türkçe boşsa ama İngilizce doluysa, onu kullan
    if "text_en" in row.index and isinstance(row["text_en"], str) and row["text_en"].strip():
        return str(row["text_en"])

    # Genel fallback (ileride başka kolon eklenirse)
    for cand in ["text", "Text", "sentence", "Sentence", "report", "description"]:
        if cand in row.index:
            val = row[cand]
            if isinstance(val, str) and val.strip():
                return str(val)

    # Hiçbir şey yoksa boş
    return ""

def load_image_tensor(img_path: str, transform):
    image = Image.open(img_path).convert("RGB")
    image_t = transform(image)  # [3, H, W]
    image_t = image_t.unsqueeze(0)  # [1, 3, H, W]
    return image_t


def overlay_heatmap_on_image(img_path: str, heatmap_color: np.ndarray, output_path: str):
    """
    heatmap_color: (H, W, 3) BGR uint8
    """
    orig = cv2.imread(img_path)  # BGR
    if orig is None:
        raise ValueError(f"Görüntü okunamadı: {img_path}")

    H, W = heatmap_color.shape[:2]
    orig_resized = cv2.resize(orig, (W, H))

    overlay = cv2.addWeighted(orig_resized, 0.5, heatmap_color, 0.5, 0)
    cv2.imwrite(output_path, overlay)


def run_explanation(
    image_path: str,
    text: str,
    device="cuda",
    checkpoint: str = "checkpoints/best_multimodal.pt",
    bert_model: str = "dbmdz/bert-base-turkish-cased",
    max_length: int = 128,
):
    """
    GUI veya başka kodlardan doğrudan çağırmak için:
      - image_path  : yüklenen resmin tam yolu
      - text        : kullanıcıdan gelen Türkçe cümle (boş string olabilir)
      - device      : "cuda" veya "cpu" ya da torch.device
      - checkpoint  : eğittiğin multimodal modelin ckpt yolu
      - bert_model  : tokenizer/model ismi
      - max_length  : BERT sequence length

    Dönüş: dict
      {
        'pred_emotion_idx', 'pred_gender_idx',
        'pred_emotion_str', 'pred_gender_str',
        'probs_emotion', 'probs_gender',
        'heatmap_emotion_color', 'heatmap_gender_color',
        'tokens_emotion', 'scores_emotion',
        'tokens_gender', 'scores_gender'
      }
    """

    # device normalize et
    if not isinstance(device, torch.device):
        device = torch.device(device if torch.cuda.is_available() else "cpu")

    # 1) Tokenizer + transform
    tokenizer = AutoTokenizer.from_pretrained(bert_model)
    _, val_tf = get_image_transforms()

    image_tensor = load_image_tensor(image_path, val_tf).to(device)

    if text is None:
        text = ""
    if not isinstance(text, str):
        text = str(text)

    enc = tokenizer(
        text if len(text) > 0 else "",
        padding="max_length",
        truncation=True,
        max_length=max_length,
        return_tensors="pt",
    )
    input_ids = enc["input_ids"].to(device)
    attention_mask = enc["attention_mask"].to(device)

    # 2) Model + checkpoint
    ckpt = torch.load(checkpoint, map_location=device)
    args_in_ckpt = ckpt.get("args", {}) or {}
    freeze_bert = args_in_ckpt.get("freeze_bert", True)
    freeze_effnet = args_in_ckpt.get("freeze_effnet", False)

    model = MultimodalEffNetBert(
        bert_model_name=bert_model,
        freeze_bert=freeze_bert,
        freeze_effnet=freeze_effnet,
    ).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    model.eval()

    # 3) Tahmin (grads kapalı)
    with torch.no_grad():
        outputs = model(
            image=image_tensor,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        logits_emotion = outputs["logits_emotion"]  # [1, 2]
        logits_gender = outputs["logits_gender"]    # [1, 2]

        probs_emotion = F.softmax(logits_emotion, dim=1)[0].cpu().numpy()
        probs_gender = F.softmax(logits_gender, dim=1)[0].cpu().numpy()

    pred_emotion_idx = int(np.argmax(probs_emotion))
    pred_gender_idx = int(np.argmax(probs_gender))

    pred_emotion_str = EMOTION_ID2STR.get(pred_emotion_idx, str(pred_emotion_idx))
    pred_gender_str = GENDER_ID2STR.get(pred_gender_idx, str(pred_gender_idx))

    # 4) Grad-CAM
    gradcam = GradCAM(model, target_layer_name=None)

    # Emotion için
    outputs_em = model(
        image=image_tensor,
        input_ids=input_ids,
        attention_mask=attention_mask,
    )
    logits_emotion_gc = outputs_em["logits_emotion"]
    heatmap_emotion_color, _ = gradcam.generate(
        image_tensor=image_tensor,
        class_logits=logits_emotion_gc,
        class_index=pred_emotion_idx,
    )

    # Gender için
    outputs_gender = model(
        image=image_tensor,
        input_ids=input_ids,
        attention_mask=attention_mask,
    )
    logits_gender_gc = outputs_gender["logits_gender"]
    heatmap_gender_color, _ = gradcam.generate(
        image_tensor=image_tensor,
        class_logits=logits_gender_gc,
        class_index=pred_gender_idx,
    )

    # 5) Text explanation (isteğe bağlı)
    tokens_emotion = scores_emotion = None
    tokens_gender = scores_gender = None

    if len(text.strip()) > 0:
        text_explainer = BertTextExplainer(model)

        tokens_emotion, scores_emotion, _ = text_explainer.explain(
            tokenizer=tokenizer,
            image_tensor=image_tensor,
            input_ids=input_ids,
            attention_mask=attention_mask,
            target="emotion",
            class_index=pred_emotion_idx,
            device=device,
        )

        tokens_gender, scores_gender, _ = text_explainer.explain(
            tokenizer=tokenizer,
            image_tensor=image_tensor,
            input_ids=input_ids,
            attention_mask=attention_mask,
            target="gender",
            class_index=pred_gender_idx,
            device=device,
        )

    return {
        "pred_emotion_idx": pred_emotion_idx,
        "pred_gender_idx": pred_gender_idx,
        "pred_emotion_str": pred_emotion_str,
        "pred_gender_str": pred_gender_str,
        "probs_emotion": probs_emotion,
        "probs_gender": probs_gender,
        "heatmap_emotion_color": heatmap_emotion_color,
        "heatmap_gender_color": heatmap_gender_color,
        "tokens_emotion": tokens_emotion,
        "scores_emotion": scores_emotion,
        "tokens_gender": tokens_gender,
        "scores_gender": scores_gender,
    }


def main():
    """
    Eski CLI akışı (CSV + id/idx) devam etsin diye
    main(), run_explanation() fonksiyonunu kullanıyor.
    GUI tarafında ise direkt run_explanation(...) çağrılacak,
    main() ile işimiz olmayacak.
    """
    args = parse_args()
    os.makedirs(args.output_dir, exist_ok=True)

    device = torch.device(args.device if torch.cuda.is_available() else "cpu")
    print("Using device:", device)

    # 1) CSV'den satırı çek
    row = load_sample_row(args.csv_path, args.id, args.idx)
    img_path = row["img_path"]
    text = get_text_from_row(row)

    true_emotion = row["emotion"] if "emotion" in row.index else None
    true_gender = row["gender"] if "gender" in row.index else None

    print(f"\nSeçilen örnek:")
    print(f"  ID      : {row['id']}")
    print(f"  img_path: {img_path}")
    print(f"  text    : {text}")
    print(f"  true emotion: {true_emotion}")
    print(f"  true gender : {true_gender}")

    # 2) Asıl işi yapan fonksiyonu çağır
    result = run_explanation(
        image_path=img_path,
        text=text,
        device=device,
        checkpoint=args.checkpoint,
        bert_model=args.bert_model,
        max_length=args.max_length,
    )

    pred_emotion_str = result["pred_emotion_str"]
    pred_gender_str = result["pred_gender_str"]
    pred_emotion_idx = result["pred_emotion_idx"]
    pred_gender_idx = result["pred_gender_idx"]
    probs_emotion = result["probs_emotion"]
    probs_gender = result["probs_gender"]
    heatmap_emotion_color = result["heatmap_emotion_color"]
    heatmap_gender_color = result["heatmap_gender_color"]
    tokens_emotion = result["tokens_emotion"]
    scores_emotion = result["scores_emotion"]
    tokens_gender = result["tokens_gender"]
    scores_gender = result["scores_gender"]

    print("\n=== Tahminler ===")
    print(f"Emotion: {pred_emotion_str} (p={probs_emotion[pred_emotion_idx]:.3f})")
    print(f"Gender : {pred_gender_str} (p={probs_gender[pred_gender_idx]:.3f})")

    # 3) Grad-CAM görsellerini diske yaz
    out_path_emotion = os.path.join(
        args.output_dir,
        f"{row['id']}_gradcam_emotion_{pred_emotion_str}.jpg",
    )
    overlay_heatmap_on_image(img_path, heatmap_emotion_color, out_path_emotion)
    print(f"Emotion Grad-CAM kaydedildi: {out_path_emotion}")

    out_path_gender = os.path.join(
        args.output_dir,
        f"{row['id']}_gradcam_gender_{pred_gender_str}.jpg",
    )
    overlay_heatmap_on_image(img_path, heatmap_gender_color, out_path_gender)
    print(f"Gender Grad-CAM kaydedildi: {out_path_gender}")

    # 4) Text explanation çıktısını terminale yaz
    if tokens_emotion is not None and scores_emotion is not None:
        def print_top_tokens(tokens, scores, title, top_k=10):
            print(f"\n--- {title} için en önemli token'lar ---")
            triplets = []
            for tok, sc in zip(tokens, scores):
                if tok in ["[CLS]", "[SEP]", "[PAD]"]:
                    continue
                triplets.append((tok, sc))
            triplets.sort(key=lambda x: x[1], reverse=True)
            for tok, sc in triplets[:top_k]:
                print(f"{tok:15s}  score={sc:.3f}")

        print_top_tokens(tokens_emotion, scores_emotion, f"Emotion ({pred_emotion_str})")

    if tokens_gender is not None and scores_gender is not None:
        def print_top_tokens2(tokens, scores, title, top_k=10):
            print(f"\n--- {title} için en önemli token'lar ---")
            triplets = []
            for tok, sc in zip(tokens, scores):
                if tok in ["[CLS]", "[SEP]", "[PAD]"]:
                    continue
                triplets.append((tok, sc))
            triplets.sort(key=lambda x: x[1], reverse=True)
            for tok, sc in triplets[:top_k]:
                print(f"{tok:15s}  score={sc:.3f}")

        print_top_tokens2(tokens_gender, scores_gender, f"Gender ({pred_gender_str})")

    if tokens_emotion is None and (text is None or not text.strip()):
        print("\nBu örnekte text bulunmadığı için text-explain atlandı.")

    print("\nİşlem tamamlandı.")


if __name__ == "__main__":
    main()
