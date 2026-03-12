import torch
import torch.nn.functional as F
from typing import List, Tuple, Optional


class BertTextExplainer:
    """
    BERT tarafı için gradient tabanlı token önem skoru hesaplar.
    MultimodalEffNetBert içinde self.bert olduğun varsayıyoruz.
    """

    def __init__(self, model):
        self.model = model
        self.model.eval()

        # Hook atacağımız modül: BERT'in embedding çıkışı
        # (Burası MultimodalEffNetBert içindeki self.bert.embeddings)
        self.emb_module = self.model.bert.embeddings

        # Her explain() çağrısı için doldurulacak
        self.emb_activations = None  # type: Optional[torch.Tensor]
        self.emb_gradients = None    # type: Optional[torch.Tensor]

        self.emb_module.register_forward_hook(self._forward_hook)
        self.emb_module.register_backward_hook(self._backward_hook)

    # ------------------ Hook fonksiyonları ------------------ #
    def _forward_hook(self, module, inputs, output):
        # output: [B, L, H]
        self.emb_activations = output

    def _backward_hook(self, module, grad_input, grad_output):
        # grad_output[0]: [B, L, H]
        self.emb_gradients = grad_output[0]

    # ------------------ Yardımcılar ------------------ #
    def _tokens_from_ids(self, tokenizer, input_ids: torch.Tensor) -> List[str]:
        """
        input_ids: [1, L]
        """
        ids = input_ids[0].detach().cpu().tolist()
        tokens = tokenizer.convert_ids_to_tokens(ids)
        return tokens

    @staticmethod
    def _normalize_scores(
        token_importance: torch.Tensor,
        attention_mask: torch.Tensor,
    ) -> List[float]:
        token_importance = token_importance.detach().cpu()

        mask = attention_mask.squeeze(0).detach().cpu()
        token_importance = token_importance * mask

        min_v = token_importance.min()
        max_v = token_importance.max()
        if max_v > min_v:
            scores = (token_importance - min_v) / (max_v - min_v)
        else:
            scores = torch.zeros_like(token_importance)

        return scores.tolist()

    @staticmethod
    def get_top_tokens(
        tokens: List[str],
        scores: List[float],
        top_k: int = 10,
        skip_special: bool = True,
    ) -> List[Tuple[str, float]]:
        """
        Token-skor listesini (tok, skor) şeklinde sıralı döndürür.
        GUI tarafında direkt kullanmak için pratik.
        """
        pairs = []
        for tok, sc in zip(tokens, scores):
            if skip_special and tok in ["[CLS]", "[SEP]", "[PAD]"]:
                continue
            pairs.append((tok, sc))

        pairs.sort(key=lambda x: x[1], reverse=True)
        return pairs[:top_k]

    # ------------------ Ana explain fonksiyonu ------------------ #
    def explain(
        self,
        tokenizer,
        image_tensor,       # [1, 3, H, W]
        input_ids,          # [1, L]
        attention_mask,     # [1, L]
        target: str = "gender",   # "gender" veya "emotion"
        class_index: int = None,
        device: torch.device = torch.device("cpu"),
    ):
        """
        Dönüş:
          - tokens: token listesi (BERT tokenları)
          - scores: her token için önem skoru (0-1 normalize)
          - pred_label_idx: kullanılan sınıf index'i
        """

        self.model.to(device)
        image_tensor = image_tensor.to(device)
        input_ids = input_ids.to(device)
        attention_mask = attention_mask.to(device)

        self.emb_activations = None
        self.emb_gradients = None
        self.model.zero_grad()
        outputs = self.model(
            image=image_tensor,
            input_ids=input_ids,
            attention_mask=attention_mask,
        )

        return self.explain_from_outputs(
            tokenizer=tokenizer,
            input_ids=input_ids,
            attention_mask=attention_mask,
            outputs=outputs,
            target=target,
            class_index=class_index,
            retain_graph=False,
        )

    def explain_from_outputs(
        self,
        tokenizer,
        input_ids,
        attention_mask,
        outputs,
        target: str = "gender",
        class_index: int = None,
        retain_graph: bool = True,
    ):
        if self.emb_activations is None:
            raise RuntimeError(
                "BertTextExplainer: activation hook'lari bos geldi. "
                "explain_from_outputs ayni forward ciktilari ile cagirilmalidir."
            )

        if target == "gender":
            logits = outputs["logits_gender"]
        else:
            logits = outputs["logits_emotion"]

        if class_index is None:
            class_index = torch.argmax(logits, dim=1).item()

        self.emb_gradients = None
        loss = logits[:, class_index].sum()
        self.model.zero_grad()
        loss.backward(retain_graph=retain_graph)

        grads = self.emb_gradients
        activations = self.emb_activations

        if grads is None or activations is None:
            raise RuntimeError(
                "BertTextExplainer: gradient veya activation hook'ları boş geldi. "
                "Muhtemelen model yapısı değişti veya backward tetiklenmedi."
            )

        token_importance = (grads * activations).sum(dim=-1).squeeze(0)

        tokens = self._tokens_from_ids(tokenizer, input_ids)
        scores = self._normalize_scores(token_importance, attention_mask)

        return tokens, scores, class_index

    def explain_targets_from_outputs(
        self,
        tokenizer,
        input_ids,
        attention_mask,
        outputs,
        targets,
    ):
        results = {}
        target_items = list(targets.items())
        for index, (target, class_index) in enumerate(target_items):
            results[target] = self.explain_from_outputs(
                tokenizer=tokenizer,
                input_ids=input_ids,
                attention_mask=attention_mask,
                outputs=outputs,
                target=target,
                class_index=class_index,
                retain_graph=index < len(target_items) - 1,
            )
        return results
