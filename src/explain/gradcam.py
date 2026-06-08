"""
Grad-CAM — image-only branch icin uyarli.

Hedef katman: ClinicalFusionClassifier.gradcam_target_layer (EfficientNet son conv blogu).
Cikti:
  generate_overlay(...) -> (overlay_pil, raw_cam_2d)
  summarize_cam_region(raw_cam) -> str  (modelin baktigi bolge ozeti)
"""

from __future__ import annotations

import io
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None) -> None:
        self.model = model
        self.target_layer = target_layer if target_layer is not None else model.gradcam_target_layer
        self._activations: Optional[torch.Tensor] = None
        self._gradients: Optional[torch.Tensor] = None
        self._handles = []
        self._register()

    def _register(self) -> None:
        def fwd(_module, _input, output):
            self._activations = output.detach()

        def bwd(_module, _grad_in, grad_out):
            self._gradients = grad_out[0].detach()

        self._handles.append(self.target_layer.register_forward_hook(fwd))
        # PyTorch >= 1.8: full_backward_hook
        self._handles.append(self.target_layer.register_full_backward_hook(bwd))

    def remove(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []

    def __del__(self):
        try:
            self.remove()
        except Exception:
            pass

    def compute(
        self,
        image: torch.Tensor,
        clinical: torch.Tensor,
        validity: torch.Tensor,
        target_class: Optional[int] = None,
    ) -> tuple[np.ndarray, int]:
        was_training = self.model.training
        self.model.eval()
        self.model.zero_grad(set_to_none=True)

        logits = self.model(image, clinical, validity)
        if target_class is None:
            target_class = int(logits.argmax(dim=1).item())
        score = logits[0, target_class]
        score.backward(retain_graph=False)

        if self._activations is None or self._gradients is None:
            raise RuntimeError("Grad-CAM hooks veri toplayamadi.")

        acts = self._activations[0]
        grads = self._gradients[0]
        weights = grads.mean(dim=(1, 2))
        cam = torch.relu((weights[:, None, None] * acts).sum(dim=0))
        cam_np = cam.cpu().numpy()
        if cam_np.max() > 0:
            cam_np = cam_np / cam_np.max()
        if was_training:
            self.model.train()
        return cam_np, target_class

    def overlay_on_image(
        self,
        cam_2d: np.ndarray,
        original_pil: Image.Image,
        alpha: float = 0.45,
    ) -> Image.Image:
        w, h = original_pil.size
        cam_resized = cv2.resize(cam_2d, (w, h))
        cam_uint8 = np.uint8(255 * cam_resized)
        heatmap = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)
        heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
        base = np.array(original_pil.convert("RGB"))
        blended = (heatmap_rgb.astype(np.float32) * alpha + base.astype(np.float32) * (1 - alpha)).clip(0, 255).astype(np.uint8)
        return Image.fromarray(blended)


def pil_to_base64_png(img: Image.Image) -> str:
    import base64
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("ascii")


def summarize_cam_region(cam_2d: np.ndarray, lang: str = "tr") -> str:
    """3x3 izgaraya ayirir, en yuksek aktivasyonun bulundugu bolgeyi sozele cevirir."""
    h, w = cam_2d.shape
    if h == 0 or w == 0:
        return "" if lang != "en" else ""
    rows = np.array_split(cam_2d, 3, axis=0)
    cell_means = np.zeros((3, 3))
    for ri in range(3):
        cols = np.array_split(rows[ri], 3, axis=1)
        for ci in range(3):
            cell_means[ri, ci] = float(cols[ci].mean())
    ri, ci = np.unravel_index(np.argmax(cell_means), cell_means.shape)
    labels_tr = [
        ["sol-ust", "ust-orta", "sag-ust"],
        ["sol-orta", "merkez", "sag-orta"],
        ["sol-alt", "alt-orta", "sag-alt"],
    ]
    labels_en = [
        ["top-left", "top-center", "top-right"],
        ["middle-left", "center", "middle-right"],
        ["bottom-left", "bottom-center", "bottom-right"],
    ]
    return labels_en[ri][ci] if lang == "en" else labels_tr[ri][ci]
