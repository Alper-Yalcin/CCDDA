"""Web logosundan (logo.svg -> project_logo.png) Windows uygulama ikonu uretir.

Cikti: installer/app_icon.ico  (PyInstaller EXE ve Inno Setup tarafindan kullanilir)

Kullanim:
    python scripts/make_app_icon.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Web'de kullanilan logonun yuksek cozunurluklu PNG render'i
SOURCE_PNG = PROJECT_ROOT / "docs" / "extracted_images_latest" / "project_logo.png"
OUTPUT_ICO = PROJECT_ROOT / "installer" / "app_icon.ico"

ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]


def main() -> None:
    if not SOURCE_PNG.exists():
        raise SystemExit(f"Kaynak logo bulunamadi: {SOURCE_PNG}")

    img = Image.open(SOURCE_PNG).convert("RGBA")

    # Kareye getir (ikon kareleri icin guvenli kenar boslugu korunur)
    side = max(img.size)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)

    OUTPUT_ICO.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT_ICO, format="ICO", sizes=[(s, s) for s in ICON_SIZES])
    print(f"Ikon olusturuldu: {OUTPUT_ICO}")


if __name__ == "__main__":
    main()
