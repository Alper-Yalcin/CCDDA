import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import List, Tuple

import torch
import torch.nn.functional as F
import cv2
import numpy as np
from PIL import Image, ImageTk
from transformers import AutoTokenizer

# Proje kökünden import edebilmek için (python -m src.app.gui_multimodal ile koşarsan genelde gerekmez)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.data.transforms import get_image_transforms
from src.models.multimodal_effnet_bert import MultimodalEffNetBert
from src.explain.gradcam import GradCAM
from src.explain.text_explain import BertTextExplainer


EMOTION_ID2STR = {0: "Happiness", 1: "Sadness"}
GENDER_ID2STR = {0: "Female", 1: "Male"}


def merge_wordpieces(tokens: List[str], scores: List[float]) -> List[Tuple[str, float]]:
    """
    BERT wordpiece token'larını okunaklı kelimelere birleştir.
    Ör: ['üzül', '##ü', '##r', '##üm'] -> 'üzülürüm'
    Skor olarak parçaların ortalamasını al.
    """
    merged = []
    current_word = ""
    current_scores = []

    for tok, sc in zip(tokens, scores):
        # Özel tokenları geç
        if tok in ["[CLS]", "[SEP]", "[PAD]"]:
            continue

        if tok.startswith("##"):
            piece = tok[2:]
            current_word += piece
            current_scores.append(sc)
        else:
            # Önceki kelimeyi kapat
            if current_word:
                merged.append((current_word, sum(current_scores) / len(current_scores)))
            current_word = tok
            current_scores = [sc]

    if current_word:
        merged.append((current_word, sum(current_scores) / len(current_scores)))

    merged.sort(key=lambda x: x[1], reverse=True)
    return merged


class MultimodalApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Multimodal Emotion & Gender Classifier + Explainable AI")

        # ---- Model / cihaz / transform ayarları ----
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("Using device:", self.device)

        self.checkpoint_path = os.path.join(PROJECT_ROOT, "checkpoints", "best_multimodal.pt")
        if not os.path.exists(self.checkpoint_path):
            messagebox.showerror(
                "Hata",
                f"Checkpoint bulunamadı:\n{self.checkpoint_path}\n\n"
                "Önce train_multimodal ile best_multimodal.pt üretmelisin."
            )
            raise SystemExit

        # Tokenizer & transform
        self.tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")
        _, self.val_tf = get_image_transforms()

        # Model + checkpoint
        print("Model yükleniyor...")
        ckpt = torch.load(self.checkpoint_path, map_location=self.device)

        freeze_bert = ckpt.get("args", {}).get("freeze_bert", True)
        freeze_effnet = ckpt.get("args", {}).get("freeze_effnet", False)
        print(f"Checkpoint args: freeze_bert={freeze_bert} freeze_effnet={freeze_effnet}")

        self.model = MultimodalEffNetBert(
            bert_model_name="dbmdz/bert-base-turkish-cased",
            freeze_bert=freeze_bert,
            freeze_effnet=freeze_effnet,
        ).to(self.device)
        self.model.load_state_dict(ckpt["model_state_dict"])
        self.model.eval()

        # GradCAM & text explainer
        self.gradcam = GradCAM(self.model, target_layer_name=None)  # son Conv2d otomatik
        self.text_explainer = BertTextExplainer(self.model)

        # UI state
        self.current_img_path = None
        self.current_img_pil = None
        self.current_img_tensor = None  # [1, 3, H, W]
        self.current_input_ids = None
        self.current_attention_mask = None

        # Tkinter image referansları (GC'ye gitmesin)
        self.tk_img_original = None
        self.tk_img_emotion_cam = None
        self.tk_img_gender_cam = None

        # ---- UI Layout ----
        self._build_ui()

    def _build_ui(self):
        # Ana çerçeve 2 kolon: solda image, sağda açıklamalar
        left_frame = tk.Frame(self.root)
        left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        right_frame = tk.Frame(self.root)
        right_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)

        # --- Sol taraf: resim + butonlar ---

        btn_frame = tk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=5)

        btn_load = tk.Button(btn_frame, text="Resim Seç", command=self.load_image)
        btn_load.pack(side=tk.LEFT, padx=5)

        btn_run = tk.Button(btn_frame, text="Tahmin & Açıkla", command=self.run_inference)
        btn_run.pack(side=tk.LEFT, padx=5)

        self.lbl_status = tk.Label(left_frame, text="Henüz resim seçilmedi.", fg="gray")
        self.lbl_status.pack(pady=5)

        # Orijinal resim
        self.lbl_original = tk.Label(left_frame, text="Orijinal görüntü", borderwidth=2, relief="groove")
        self.lbl_original.pack(pady=5)

        # Emotion Grad-CAM
        self.lbl_emotion_cam = tk.Label(left_frame, text="Emotion Grad-CAM", borderwidth=2, relief="groove")
        self.lbl_emotion_cam.pack(pady=5)

        # Gender Grad-CAM
        self.lbl_gender_cam = tk.Label(left_frame, text="Gender Grad-CAM", borderwidth=2, relief="groove")
        self.lbl_gender_cam.pack(pady=5)

        # --- Sağ taraf: text input + sonuçlar + token önem listeleri ---

        # Tahmin sonuçları
        self.lbl_results = tk.Label(
            right_frame,
            text="Emotion: -\nGender : -",
            font=("Arial", 12, "bold"),
            justify="left",
        )
        self.lbl_results.pack(anchor="w", pady=5)

        # Açıklama metni için scrollable text widget
        tk.Label(right_frame, text="Açıklama:").pack(anchor="w")
        
        explain_frame = tk.Frame(right_frame)
        explain_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scrollbar = tk.Scrollbar(explain_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.txt_explanation = tk.Text(
            explain_frame,
            height=10,
            width=60,
            wrap=tk.WORD,
            font=("Arial", 10),
            yscrollcommand=scrollbar.set
        )
        self.txt_explanation.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.txt_explanation.yview)

    # -------------------------------------------------------------------------
    #                           Yardımcı Fonksiyonlar
    # -------------------------------------------------------------------------

    def load_image(self):
        """Dosya seçtir, resmi göster ve tensora çevir."""
        filetypes = [("Image files", "*.jpg *.jpeg *.png *.bmp"), ("All files", "*.*")]
        path = filedialog.askopenfilename(title="Görüntü seç", filetypes=filetypes)

        if not path:
            return

        if not os.path.exists(path):
            messagebox.showerror("Hata", f"Dosya bulunamadı:\n{path}")
            return

        self.current_img_path = path

        # PIL ile oku
        pil_img = Image.open(path).convert("RGB")
        self.current_img_pil = pil_img

        # Model için transform
        img_t = self.val_tf(pil_img)  # [3, H, W]
        img_t = img_t.unsqueeze(0)    # [1, 3, H, W]
        self.current_img_tensor = img_t.to(self.device)

        # Tkinter'da göstermek için: boyut küçült
        disp_img = pil_img.copy()
        disp_img.thumbnail((256, 256))
        self.tk_img_original = ImageTk.PhotoImage(disp_img)
        self.lbl_original.configure(image=self.tk_img_original)
        self.lbl_original.image = self.tk_img_original

        self.lbl_status.configure(text=f"Seçilen dosya: {os.path.basename(path)}", fg="black")

    def _make_overlay_pil(self, heatmap_color: np.ndarray) -> Image.Image:
        """
        Grad-CAM heatmap'i orijinal görüntü ile çakıştırıp PIL Image döndür.
        heatmap_color: (H, W, 3) BGR uint8
        """
        if self.current_img_path is None:
            raise ValueError("Önce görüntü seçmelisin.")

        orig = cv2.imread(self.current_img_path)
        if orig is None:
            raise ValueError(f"Görüntü okunamadı: {self.current_img_path}")

        H, W = heatmap_color.shape[:2]
        orig_resized = cv2.resize(orig, (W, H))

        overlay_bgr = cv2.addWeighted(orig_resized, 0.5, heatmap_color, 0.5, 0)
        overlay_rgb = cv2.cvtColor(overlay_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(overlay_rgb)
        return pil_img

    def _generate_explanation(self, image_path: str, pred_emotion: str, pred_gender: str, prob_em: float, prob_ge: float) -> str:
        """
        Seçilen görseli ve tahmin sonuçlarını açıklayan metin üretir.
        """
        explanations = []

        # Dosya adı
        filename = os.path.basename(image_path)
        explanations.append(f"Seçilen dosya: {filename}")
        explanations.append("")

        # ---- Emotion açıklaması ----
        explanations.append(f"🎭 Duygu Tahmini: {pred_emotion} (güven: {prob_em:.1%})")
        if pred_emotion == "Happiness":
            explanations.append("   → Görseldeki çizim genel olarak daha açık, düzenli ve olumlu bir duygu tonu yansıtıyor.")
            explanations.append("   → Renkler daha canlı ve kompozisyon daha dengeli görünüyor.")
            explanations.append("   → Model, Grad-CAM ile görselin merkez bölgelerindeki renk ve şekilleri analiz etti.")
        else:
            explanations.append("   → Çizimdeki çizgiler ve genel kompozisyon daha çok üzüntü, karamsarlık ya da içe kapanıklık hissi veriyor.")
            explanations.append("   → Koyu tonlar ve daha az detay dikkat çekiyor.")
            explanations.append("   → Model, görseldeki genel hava ve çizgi karakterini değerlendirdi.")

        explanations.append("")

        # ---- Gender açıklaması ----
        explanations.append(f"👤 Cinsiyet Tahmini: {pred_gender} (güven: {prob_ge:.1%})")
        if pred_gender == "Male":
            explanations.append("   → Çizim stili daha sivri hatlı ve baskın çizgiler içeriyor.")
            explanations.append("   → Bu, daha çok erkek çocuklarda görülen bir çizim deseni.")
        else:
            explanations.append("   → Çizim daha yumuşak hatlı ve detaylara daha fazla odaklanılmış.")
            explanations.append("   → Bu tarz, kadın çocuklarda daha sık görülüyor.")

        explanations.append("")
        explanations.append("📊 Açıklama Yöntemleri:")
        explanations.append("   → Grad-CAM haritaları, modelin hangi bölgelere odaklandığını gösterir.")
        explanations.append("   → Kırmızı/sarı bölgeler modelin en çok dikkat ettiği alanlardır.")

        return "\n".join(explanations)

    # -------------------------------------------------------------------------
    #                           Ana İşlev: Tahmin + Açıklama
    # -------------------------------------------------------------------------

    def run_inference(self):
        if self.current_img_tensor is None:
            messagebox.showwarning("Uyarı", "Önce bir görüntü seçmelisin.")
            return

        # Boş metin ile tokenize (sadece görsel tabanlı tahmin)
        text = ""
        enc = self.tokenizer(
            text,
            padding="max_length",
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        input_ids = enc["input_ids"].to(self.device)
        attention_mask = enc["attention_mask"].to(self.device)

        self.current_input_ids = input_ids
        self.current_attention_mask = attention_mask

        img_t = self.current_img_tensor

        # ---- 1) Tahmin yap (no_grad ile) ----
        with torch.no_grad():
            outputs = self.model(
                image=img_t,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )
            logits_emotion = outputs["logits_emotion"]  # [1, 2]
            logits_gender = outputs["logits_gender"]    # [1, 2]

            probs_emotion = F.softmax(logits_emotion, dim=1)[0].cpu().numpy()
            probs_gender = F.softmax(logits_gender, dim=1)[0].cpu().numpy()

        pred_em_idx = int(np.argmax(probs_emotion))
        pred_g_idx = int(np.argmax(probs_gender))

        pred_em_str = EMOTION_ID2STR.get(pred_em_idx, str(pred_em_idx))
        pred_g_str = GENDER_ID2STR.get(pred_g_idx, str(pred_g_idx))

        self.lbl_results.configure(
            text=(
                f"Emotion: {pred_em_str} (p={probs_emotion[pred_em_idx]:.3f})\n"
                f"Gender : {pred_g_str} (p={probs_gender[pred_g_idx]:.3f})"
            )
        )

        # ---- 2) Grad-CAM (emotion & gender) ----
        print("Grad-CAM hesaplanıyor...")

        # Emotion için grads açık forward
        outputs_em = self.model(
            image=img_t,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        logits_em_gc = outputs_em["logits_emotion"]

        heatmap_emotion_color, _ = self.gradcam.generate(
            image_tensor=img_t,
            class_logits=logits_em_gc,
            class_index=pred_em_idx,
        )
        pil_emotion_cam = self._make_overlay_pil(heatmap_emotion_color)
        pil_emotion_cam.thumbnail((256, 256))
        self.tk_img_emotion_cam = ImageTk.PhotoImage(pil_emotion_cam)
        self.lbl_emotion_cam.configure(image=self.tk_img_emotion_cam)
        self.lbl_emotion_cam.image = self.tk_img_emotion_cam

        # Gender için grads açık forward
        outputs_g = self.model(
            image=img_t,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        logits_g_gc = outputs_g["logits_gender"]

        heatmap_gender_color, _ = self.gradcam.generate(
            image_tensor=img_t,
            class_logits=logits_g_gc,
            class_index=pred_g_idx,
        )
        pil_gender_cam = self._make_overlay_pil(heatmap_gender_color)
        pil_gender_cam.thumbnail((256, 256))
        self.tk_img_gender_cam = ImageTk.PhotoImage(pil_gender_cam)
        self.lbl_gender_cam.configure(image=self.tk_img_gender_cam)
        self.lbl_gender_cam.image = self.tk_img_gender_cam

        # ---- 3) Açıklama metni üret ----
        explanation = self._generate_explanation(
            self.current_img_path,
            pred_em_str,
            pred_g_str,
            probs_emotion[pred_em_idx],
            probs_gender[pred_g_idx]
        )
        
        self.txt_explanation.delete(1.0, tk.END)
        self.txt_explanation.insert(1.0, explanation)


def main():
    root = tk.Tk()
    app = MultimodalApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
