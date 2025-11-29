import torch
import torch.nn as nn
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
    ):
        super().__init__()

        # --- Image encoder: EfficientNet-B0 ---
        weights = EfficientNet_B0_Weights.IMAGENET1K_V1
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

    def forward(self, image, input_ids, attention_mask):
        """
        image: [B, 3, H, W]
        input_ids: [B, L]
        attention_mask: [B, L]
        """
        # --- Image branch ---
        x = self.effnet_features(image)          # [B, C, H', W']
        x = self.effnet_pool(x)                  # [B, C, 1, 1]
        x = torch.flatten(x, 1)                  # [B, C]
        img_emb = self.img_proj(x)               # [B, proj_dim]

        # --- Text branch ---
        bert_out = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask,
        )
        # CLS token embedding
        cls_emb = bert_out.last_hidden_state[:, 0, :]  # [B, text_embedding_dim]
        text_emb = self.text_proj(cls_emb)             # [B, proj_dim]

        # --- Fusion ---
        fused = torch.cat([img_emb, text_emb], dim=1)  # [B, 2*proj_dim]

        # --- Heads ---
        logits_emotion = self.emotion_head(fused)      # [B, 2]
        logits_gender = self.gender_head(fused)        # [B, 2]

        return {
            "logits_emotion": logits_emotion,
            "logits_gender": logits_gender,
            "img_emb": img_emb,
            "text_emb": text_emb,
            "fused": fused,
        }
