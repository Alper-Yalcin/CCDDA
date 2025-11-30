import torch
import torch.nn as nn
import torch.nn.functional as F
import cv2
import numpy as np


class GradCAM:
    def __init__(self, model, target_layer_name=None):
        """
        target_layer_name:
          - "modeldeki.attr.yolu" (örn: 'image_backbone.features')
          - None ise: model içindeki son Conv2d katmanı otomatik seçilir.
        """
        self.model = model
        self.model.eval()

        self.target_layer = self._get_target_layer(target_layer_name)

        # Hooks
        self.activations = None
        self.gradients = None

        self.target_layer.register_forward_hook(self._forward_hook)
        self.target_layer.register_backward_hook(self._backward_hook)

    def _get_target_layer(self, name):
        # Önce isimle bulmayı dene
        if name is not None and name != "":
            module = self.model
            try:
                for attr in name.split("."):
                    module = getattr(module, attr)
                print(f"[GradCAM] Using target layer by name: {name}")
                return module
            except AttributeError:
                print(f"[GradCAM] Uyarı: '{name}' bulunamadı, otomatik Conv2d aramaya geçiyorum...")

        # Fallback: model içindeki son Conv2d katmanını bul
        target = None
        for m in self.model.modules():
            if isinstance(m, nn.Conv2d):
                target = m

        if target is None:
            raise ValueError("[GradCAM] Model içinde Conv2d katmanı bulunamadı, uygun layer ismi vermen gerekiyor.")

        print(f"[GradCAM] Using last Conv2d layer as target: {target}")
        return target

    def _forward_hook(self, module, input, output):
        self.activations = output.detach()

    def _backward_hook(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, image_tensor, class_logits, class_index=None):
        """
        image_tensor : (1, 3, H, W)
        class_logits : logits for emotion or gender
        class_index  : which class to visualize
        """

        if class_index is None:
            class_index = torch.argmax(class_logits).item()

        loss = class_logits[:, class_index].sum()
        self.model.zero_grad()
        loss.backward(retain_graph=True)

        # Gradients shape: (1, C, H', W')
        # Activations shape: (1, C, H', W')

        weights = torch.mean(self.gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * self.activations, dim=1).squeeze()

        cam = torch.relu(cam)
        cam = cam / torch.max(cam)

        cam = cam.cpu().numpy()
        cam = cv2.resize(cam, (image_tensor.size(3), image_tensor.size(2)))
        heatmap = (cam * 255).astype(np.uint8)

        heatmap_color = cv2.applyColorMap(heatmap, cv2.COLORMAP_JET)

        return heatmap_color, cam
