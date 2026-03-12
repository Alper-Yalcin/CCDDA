import torch
import torch.nn as nn
from typing import Dict                     # ← EKLENEN SATIR
from torchvision.models import efficientnet_b0, EfficientNet_B0_Weights
from transformers import AutoModel

class MultimodalEffNetBert(nn.Module):
    def __init__(
        self,
        bert_model_name: str = "dbmdz/bert-base-turkish-cased",
        img_embedding_dim: int = 1280,   # EfficientNet-B0 çıkışı
        text_embedding_dim: int = 768,   # BERT base çıkışı
        proj_dim: int = 512,
        freeze_bert: bool = True,
        freeze_effnet: bool = True,
        use_imagenet_weights: bool = True,
    ):
        super().__init__()

        # --- Image encoder: EfficientNet-B0 ---
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1 if use_imagenet_weights else None
        effnet = efficientnet_b0(weights=weights)

        # classifier'ı at, sadece feature extractor kullan
        self.effnet_features = effnet.features
        self.effnet_pool = nn.AdaptiveAvgPool2d(1)  # [B, C, 1, 1] → [B, C]

        # --- Text encoder: BERT ---
        self.bert = AutoModel.from_pretrained(bert_model_name)

        # Freeze ayarları
        if freeze_effnet:
            for p in self.effnet_features.parameters():
                p.requires_grad = False

        if freeze_bert:
            for p in self.bert.parameters():
                p.requires_grad = False

        # --- Projection layers ---
        self.img_proj = nn.Sequential(
            nn.Linear(img_embedding_dim, proj_dim),
            nn.ReLU(),
        )
        self.text_proj = nn.Sequential(
            nn.Linear(text_embedding_dim, proj_dim),
            nn.ReLU(),
        )

        fusion_dim = proj_dim * 2

        # --- Heads ---
        self.emotion_head = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, 2),  # Happiness / Sadness
        )

        self.gender_head = nn.Sequential(
            nn.Linear(fusion_dim, 256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, 2),  # Female / Male
        )

    def encode_image(self, image: torch.Tensor) -> torch.Tensor:
        """
        Sadece görüntüden embedding üretir.
        image: [B, 3, H, W]
        return: img_emb [B, proj_dim]
        """
        x_img = self.effnet_features(image)            # [B, C, H', W']
        x_img = self.effnet_pool(x_img)                # [B, C, 1, 1]
        x_img = x_img.view(x_img.size(0), -1)          # [B, C]
        img_emb = self.img_proj(x_img)                 # [B, proj_dim]
        return img_emb

    def encode_text(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> torch.Tensor:
        """
        Sadece metinden embedding üretir (CLS üzerinden).
        input_ids: [B, L]
        attention_mask: [B, L]
        return: text_emb [B, proj_dim]
        """
        bert_out = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        cls_emb = bert_out.last_hidden_state[:, 0, :]  # [B, hidden]
        text_emb = self.text_proj(cls_emb)             # [B, proj_dim]
        return text_emb

    def encode_multimodal(
        self,
        image: torch.Tensor,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Görüntü + metni birlikte encode eder,
        hem tekil embedding'leri hem de fused embedding'i döner.
        """
        img_emb = self.encode_image(image)                      # [B, proj_dim]
        text_emb = self.encode_text(input_ids, attention_mask)  # [B, proj_dim]

        # Burada ekstra bir fully-connected katmana gerek yok;
        # direkt concatenation sonrası head'lere vereceğiz.
        fused = torch.cat([img_emb, text_emb], dim=1)           # [B, 2*proj_dim]

        return {
            "img_emb": img_emb,
            "text_emb": text_emb,
            "fused": fused,
        }

    def forward(
        self,
        image: torch.Tensor,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Ana forward:
          - emotion & gender logits
          - img_emb, text_emb ve fused embedding
        """
        feats = self.encode_multimodal(
            image=image,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        fused = feats["fused"]

        # Sınıflandırma başlıkları
        logits_emotion = self.emotion_head(fused)  # [B, 2]
        logits_gender = self.gender_head(fused)    # [B, 2]

        return {
            "logits_emotion": logits_emotion,
            "logits_gender": logits_gender,
            "img_emb": feats["img_emb"],
            "text_emb": feats["text_emb"],
            "fused": fused,
        }
