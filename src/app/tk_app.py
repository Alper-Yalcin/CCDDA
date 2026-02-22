import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

import torch
import torch.nn.functional as F
from transformers import AutoTokenizer

# Proje kökünden import edebilmek için
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from src.models.multimodal_effnet_bert import MultimodalEffNetBert
from src.data.transforms import get_image_transforms

# ----------------------------
# ID2STR HARİTALARI
# ----------------------------
EMOTION_ID2STR = {0: "Happiness", 1: "Sadness"}
GENDER_ID2STR = {0: "Female", 1: "Male"}


# ----------------------------
# Otomatik açıklama üretici
# ----------------------------
def generate_explanation(pred_emotion, pred_gender, img_emb, text_emb=None):
    """
    Çok basit ama mantıklı açıklamalar döner.
    İstersen burayı daha da güçlendirebiliriz (LLM’e bağlama vs.)
    """
    explanations = []

    # ---- Emotion açıklaması ----
    if pred_emotion == "Happiness":
        explanations.append("Görseldeki çizim genel olarak daha açık, düzenli ve olumlu bir duygu tonu yansıtıyor.")
    else:
        explanations.append("Çizimdeki çizgiler ve genel kompozisyon daha çok üzüntü, karamsarlık ya da içe kapanıklık hissi veriyor.")

    # ---- Gender açıklaması ----
    if pred_gender == "Male":
        explanations.append("Çizim stili daha sivri hatlı ve baskın çizgiler içeriyor. Bu, daha çok erkek çocuklarda görülen bir desen.")
    else:
        explanations.append("Çizim daha yumuşak hatlı ve detaylara daha fazla odaklanılmış. Bu, kadın çocuklarda daha sık görülüyor.")

    # Eğer text varsa (embedding geldiyse) küçük bir yorum ekle
    if text_emb is not None:
        explanations.append("Metin girdisi de modelin kararını desteklemiş görünüyor.")

    return "\n".join(explanations)


# ----------------------------
# Tkinter Uygulaması
# ----------------------------
class EmotionGenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multimodal Emotion + Gender Classifier with Explanation")
        self.root.geometry("900x700")

        # Model
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self.transform = None

        self._load_model()

        # UI ELEMANLARI
        self.image_panel = tk.Label(self.root)
        self.image_panel.pack(pady=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack()

        self.btn_open = tk.Button(btn_frame, text="Fotoğraf Seç", command=self.load_image)
        self.btn_open.grid(row=0, column=0, padx=10)

        self.btn_predict = tk.Button(btn_frame, text="Tahmin Et", command=self.predict)
        self.btn_predict.grid(row=0, column=1, padx=10)

        self.result_label = tk.Label(self.root, text="", font=("Arial", 14), justify="left")
        self.result_label.pack(pady=10)

        # Açıklama metni için text widget (scrollbar ile)
        explain_frame = tk.Frame(self.root)
        explain_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(explain_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.explain_text = tk.Text(
            explain_frame,
            font=("Arial", 11),
            wrap=tk.WORD,
            height=15,
            yscrollcommand=scrollbar.set
        )
        self.explain_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.explain_text.yview)

        self.current_image_path = None

    # ----------------------------
    # MODELİ YÜKLE
    # ----------------------------
    def _load_model(self):
        try:
            # Checkpoint yükle
            ckpt_path = os.path.join(PROJECT_ROOT, "checkpoints", "best_multimodal.pt")
            print("Loading checkpoint:", ckpt_path)

            ckpt = torch.load(ckpt_path, map_location=self.device)

            freeze_bert = ckpt.get("args", {}).get("freeze_bert", True)
            freeze_effnet = ckpt.get("args", {}).get("freeze_effnet", False)

            self.tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")
            _, val_tf = get_image_transforms()
            self.transform = val_tf

            # Model
            self.model = MultimodalEffNetBert(
                bert_model_name="dbmdz/bert-base-turkish-cased",
                freeze_bert=freeze_bert,
                freeze_effnet=freeze_effnet,
            ).to(self.device)

            self.model.load_state_dict(ckpt["model_state_dict"])
            self.model.eval()

            print("Model loaded successfully.")

        except Exception as e:
            print("Model load error:", e)
            messagebox.showerror("Hata", "Model yüklenemedi.")

    # ----------------------------
    # FOTOĞRAF YÜKLEME
    # ----------------------------
    def load_image(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg;*.png;*.jpeg")]
        )
        if not filepath:
            return

        self.current_image_path = filepath
        img = Image.open(filepath)
        img = img.resize((400, 400))
        img_tk = ImageTk.PhotoImage(img)

        self.image_panel.configure(image=img_tk)
        self.image_panel.image = img_tk

        self.result_label.config(text="")
        self.explain_text.delete(1.0, tk.END)

    # ----------------------------
    # TAHMİN
    # ----------------------------
    def predict(self):
        if self.current_image_path is None:
            messagebox.showwarning("Uyarı", "Lütfen bir görsel seçin.")
            return

        # Görsel oku
        image = Image.open(self.current_image_path).convert("RGB")
        img_tensor = self.transform(image).unsqueeze(0).to(self.device)

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

        # Model forward
        with torch.no_grad():
            out = self.model(
                image=img_tensor,
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

        # Tahmin
        emotion_logits = out["logits_emotion"]
        gender_logits = out["logits_gender"]

        prob_em = F.softmax(emotion_logits, dim=1)[0]
        prob_ge = F.softmax(gender_logits, dim=1)[0]

        pred_em = EMOTION_ID2STR[int(torch.argmax(prob_em))]
        pred_ge = GENDER_ID2STR[int(torch.argmax(prob_ge))]

        prob_em_val = prob_em.max().item()
        prob_ge_val = prob_ge.max().item()

        # Otomatik açıklama
        explanation = generate_explanation(
            self.current_image_path,
            pred_em,
            pred_ge,
            prob_em_val,
            prob_ge_val
        )

        # Arayüze yaz
        result_text = (
            f"Emotion: {pred_em} ({prob_em_val:.3f})\n"
            f"Gender : {pred_ge} ({prob_ge_val:.3f})"
        )
        self.result_label.config(text=result_text)

        self.explain_text.delete(1.0, tk.END)
        self.explain_text.insert(1.0, explanation)


# ----------------------------
# UYGULAMAYI BAŞLAT
# ----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = EmotionGenderApp(root)
    root.mainloop()
