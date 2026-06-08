from typing import Tuple
from torchvision import transforms


def get_image_transforms(
    image_size: int = 224,
) -> Tuple[transforms.Compose, transforms.Compose]:
    """
    Train ve val/test için iki ayrı transform döndürür.
    """
    # NOT: HorizontalFlip cikarildi. Cocuk cizimlerinde sol/sag yerlesim
    # klinik anlam tasiyor (CV/klinik raporlari).
    train_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.RandomRotation(degrees=10),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    val_transform = transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225],
        ),
    ])

    return train_transform, val_transform
