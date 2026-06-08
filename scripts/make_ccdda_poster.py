from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "out"

W, H = 4960, 7016  # A0 ratio at 150 dpi
BG = "#FEFDFB"
NAVY = "#111827"
TEXT = "#293241"
MUTED = "#667085"
LINE = "#168A8A"
LINE_DARK = "#0B6F73"
ORANGE = "#E76F3C"
GREEN = "#5BAE7B"
BLUE = "#2F80ED"
PURPLE = "#8B5CF6"
CARD = "#FFFFFF"
CARD_STROKE = "#E5E7EB"
SOFT = "#F6F8FA"


def font_path(name: str) -> Path:
    candidates = [
        Path("C:/Windows/Fonts") / name,
        Path("/usr/share/fonts/truetype/dejavu") / name,
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(name)


FONT_REG = font_path("arial.ttf")
FONT_BOLD = font_path("arialbd.ttf")
FONT_ITALIC = font_path("ariali.ttf")


def f(size: int, bold: bool = False, italic: bool = False) -> ImageFont.FreeTypeFont:
    if italic:
        return ImageFont.truetype(str(FONT_ITALIC), size)
    return ImageFont.truetype(str(FONT_BOLD if bold else FONT_REG), size)


def bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = word if not current else f"{current} {word}"
        if bbox(draw, trial, font)[0] <= max_width:
            current = trial
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.FreeTypeFont,
    fill: str = TEXT,
    leading: int | None = None,
    align: str = "left",
) -> int:
    if leading is None:
        leading = int(font.size * 1.22)
    for line in wrap_text(draw, text, font, max_width):
        tw, _ = bbox(draw, line, font)
        dx = 0
        if align == "center":
            dx = (max_width - tw) // 2
        elif align == "right":
            dx = max_width - tw
        draw.text((x + dx, y), line, font=font, fill=fill)
        y += leading
    return y


def draw_centered(draw: ImageDraw.ImageDraw, text: str, cx: int, y: int, font: ImageFont.FreeTypeFont, fill: str) -> int:
    tw, th = bbox(draw, text, font)
    draw.text((cx - tw // 2, y), text, font=font, fill=fill)
    return y + th


def section_title(draw: ImageDraw.ImageDraw, title: str, x: int, y: int) -> int:
    draw.text((x, y), title, font=f(68, bold=True), fill=NAVY)
    tw, th = bbox(draw, title, f(68, bold=True))
    draw.rounded_rectangle((x, y + th + 18, x + min(tw, 380), y + th + 29), radius=5, fill=LINE)
    return y + th + 58


def bullet_list(
    draw: ImageDraw.ImageDraw,
    items: list[str],
    x: int,
    y: int,
    max_width: int,
    font: ImageFont.FreeTypeFont,
    bullet_color: str = LINE,
    leading: int | None = None,
) -> int:
    if leading is None:
        leading = int(font.size * 1.25)
    for item in items:
        draw.ellipse((x, y + 15, x + 15, y + 30), fill=bullet_color)
        y = draw_wrapped(draw, item, x + 42, y, max_width - 42, font, fill=TEXT, leading=leading)
        y += 22
    return y


def rounded_image(
    base: Image.Image,
    path: Path,
    box: tuple[int, int, int, int],
    radius: int = 28,
    mode: str = "contain",
    bg: str = "#FFFFFF",
) -> None:
    x1, y1, x2, y2 = box
    bw, bh = x2 - x1, y2 - y1
    im = Image.open(path).convert("RGBA")
    if mode == "cover":
        scale = max(bw / im.width, bh / im.height)
        nw, nh = int(im.width * scale), int(im.height * scale)
        im = im.resize((nw, nh), Image.LANCZOS)
        left = (nw - bw) // 2
        top = (nh - bh) // 2
        im = im.crop((left, top, left + bw, top + bh))
    else:
        im.thumbnail((bw, bh), Image.LANCZOS)
        canvas = Image.new("RGBA", (bw, bh), bg)
        canvas.alpha_composite(im, ((bw - im.width) // 2, (bh - im.height) // 2))
        im = canvas

    mask = Image.new("L", (bw, bh), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, bw, bh), radius=radius, fill=255)
    base.alpha_composite(im, (x1, y1))
    if radius:
        # Re-mask pasted area by rebuilding with transparency to keep corners clean.
        area = base.crop((x1, y1, x2, y2))
        transparent = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
        transparent.alpha_composite(area)
        transparent.putalpha(mask)
        base.paste(transparent, (x1, y1), transparent)


def card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int = 28, fill: str = CARD) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=CARD_STROKE, width=2)


def metric_card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], value: str, label: str, accent: str) -> None:
    x1, y1, x2, y2 = box
    card(draw, box, radius=26)
    draw.rounded_rectangle((x1, y1, x2, y1 + 12), radius=6, fill=accent)
    draw_wrapped(draw, value, x1 + 28, y1 + 36, x2 - x1 - 56, f(64, bold=True), fill=NAVY, leading=70, align="center")
    draw_wrapped(draw, label, x1 + 30, y1 + 122, x2 - x1 - 60, f(30, bold=True), fill=MUTED, leading=38, align="center")


def draw_arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int], end: tuple[int, int], color: str = LINE_DARK) -> None:
    draw.line((*start, *end), fill=color, width=7)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    length = 28
    a1 = angle + math.pi * 0.84
    a2 = angle - math.pi * 0.84
    p1 = (end[0] + int(math.cos(a1) * length), end[1] + int(math.sin(a1) * length))
    p2 = (end[0] + int(math.cos(a2) * length), end[1] + int(math.sin(a2) * length))
    draw.polygon([end, p1, p2], fill=color)


def pipeline_icon(draw: ImageDraw.ImageDraw, kind: str, cx: int, cy: int, color: str) -> None:
    if kind == "image":
        draw.rounded_rectangle((cx - 34, cy - 28, cx + 34, cy + 28), radius=8, outline=color, width=5)
        draw.line((cx - 26, cy + 12, cx - 6, cy - 8, cx + 8, cy + 8, cx + 28, cy - 14), fill=color, width=4)
        draw.ellipse((cx - 20, cy - 18, cx - 10, cy - 8), outline=color, width=4)
    elif kind == "brain":
        for dx, dy in [(-20, -12), (0, -18), (20, -10), (-12, 10), (12, 12)]:
            draw.ellipse((cx + dx - 12, cy + dy - 12, cx + dx + 12, cy + dy + 12), outline=color, width=4)
        draw.line((cx - 34, cy, cx + 34, cy), fill=color, width=4)
    elif kind == "gauge":
        draw.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), outline=color, width=5)
        for a in range(210, 331, 30):
            r = math.radians(a)
            draw.line((cx + math.cos(r) * 25, cy + math.sin(r) * 25, cx + math.cos(r) * 34, cy + math.sin(r) * 34), fill=color, width=3)
        draw.line((cx, cy, cx + 22, cy - 18), fill=color, width=5)
    elif kind == "bottle":
        draw.rounded_rectangle((cx - 30, cy - 38, cx + 30, cy + 38), radius=12, outline=color, width=5)
        draw.rectangle((cx - 15, cy - 55, cx + 15, cy - 35), outline=color, width=5)
        draw.line((cx - 18, cy + 4, cx - 3, cy + 18, cx + 24, cy - 18), fill=color, width=5)
    elif kind == "chat":
        draw.rounded_rectangle((cx - 38, cy - 28, cx + 38, cy + 22), radius=8, outline=color, width=5)
        draw.polygon([(cx - 8, cy + 22), (cx + 10, cy + 22), (cx + 1, cy + 38)], outline=color, fill=None)
        draw.line((cx - 22, cy - 8, cx + 20, cy - 8), fill=color, width=4)
        draw.line((cx - 22, cy + 8, cx + 10, cy + 8), fill=color, width=4)
    else:
        draw.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), outline=color, width=5)
        draw.arc((cx - 20, cy - 6, cx + 20, cy + 24), 10, 170, fill=color, width=4)
        draw.ellipse((cx - 18, cy - 16, cx - 8, cy - 6), fill=color)
        draw.ellipse((cx + 8, cy - 16, cx + 18, cy - 6), fill=color)


def draw_pipeline(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    card(draw, box, radius=22, fill="#F8FBFB")
    draw.text((x1 + 46, y1 + 38), "SİSTEM AKIŞI", font=f(48, bold=True), fill=NAVY)
    draw.rounded_rectangle((x1 + 46, y1 + 100, x1 + 310, y1 + 110), radius=5, fill=LINE)
    steps = [
        ("1", "Çizim", "Girdisi", BLUE),
        ("2", "ResNet-50", "Özellik", LINE),
        ("3", "16 Klinik", "Gösterge", ORANGE),
        ("4", "Concept", "Bottleneck", PURPLE),
        ("5", "Grad-CAM", "+ LLM", LINE_DARK),
        ("6", "Duygu", "Çıktısı", GREEN),
    ]
    n = len(steps)
    radius = 52
    margin = 150
    sx = x1 + margin
    cy = y1 + 230
    gap = (x2 - x1 - 2 * margin) // (n - 1)
    points = [(sx + i * gap, cy) for i in range(n)]
    for start, end in zip(points, points[1:]):
        draw_arrow(draw, (start[0] + radius + 10, cy), (end[0] - radius - 10, cy))
    for (num, a, b, color), (cx, _) in zip(steps, points):
        # Yumuşak halka + dolu daire içinde adım numarası
        draw.ellipse((cx - radius - 9, cy - radius - 9, cx + radius + 9, cy + radius + 9), fill="#FFFFFF", outline=color, width=4)
        draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius), fill=color)
        nw, nh = bbox(draw, num, f(56, bold=True))
        draw.text((cx - nw // 2, cy - nh // 2 - 6), num, font=f(56, bold=True), fill="#FFFFFF")
        draw_centered(draw, a, cx, cy + radius + 30, f(30, bold=True), NAVY)
        draw_centered(draw, b, cx, cy + radius + 68, f(30, bold=True), MUTED)


def draw_bar_chart(draw: ImageDraw.ImageDraw, x: int, y: int, width: int, data: list[tuple[str, float, str]]) -> int:
    row_h = 78
    label_w = 430
    bar_w = width - label_w - 120
    draw.text((x, y), "Sınıf Bazında F1", font=f(48, bold=True), fill=NAVY)
    y += 74
    for label, value, color in data:
        draw.text((x, y + 10), label, font=f(33, bold=True), fill=TEXT)
        bx = x + label_w
        by = y + 14
        draw.rounded_rectangle((bx, by, bx + bar_w, by + 28), radius=14, fill="#E9EEF3")
        draw.rounded_rectangle((bx, by, bx + int(bar_w * value), by + 28), radius=14, fill=color)
        draw.text((bx + bar_w + 28, y + 5), f"{value:.3f}".replace(".", ","), font=f(32, bold=True), fill=NAVY)
        y += row_h
    return y


def draw_model_compare(draw: ImageDraw.ImageDraw, x: int, y: int, width: int) -> int:
    draw.text((x, y), "Nihai Model Karşılaştırması", font=f(46, bold=True), fill=NAVY)
    y += 70
    data = [
        ("ResNet-50 görüntü", 0.826, BLUE),
        ("ResNet-50 + klinik", 0.821, ORANGE),
        ("Kavram Darboğazı", 0.834, GREEN),
    ]
    label_w = 520
    bar_w = width - label_w - 120
    for label, value, color in data:
        draw.text((x, y + 4), label, font=f(31, bold=True), fill=TEXT)
        bx = x + label_w
        draw.rounded_rectangle((bx, y + 11, bx + bar_w, y + 39), radius=14, fill="#E9EEF3")
        draw.rounded_rectangle((bx, y + 11, bx + int(bar_w * ((value - 0.78) / 0.06)), y + 39), radius=14, fill=color)
        draw.text((bx + bar_w + 28, y + 1), f"{value:.3f}".replace(".", ","), font=f(31, bold=True), fill=NAVY)
        y += 66
    return y + 20


FIDELITY_DATA: list[tuple[str, float]] = [
    ("Bileşen sayısı", 0.95),
    ("Koyu renk oranı", 0.94),
    ("Figür alanı", 0.92),
    ("Boş alan oranı", 0.92),
    ("Çizgi koyuluğu", 0.89),
    ("Gölgeleme", 0.87),
    ("Dikey konum", 0.85),
    ("Renk sıcaklığı", 0.85),
    ("Form bütünlüğü", 0.80),
    ("Baskı değişimi", 0.77),
    ("Figür boyutu", 0.77),
    ("Parça kopukluğu", 0.73),
    ("Merkezilik", 0.63),
    ("Keskin açı oranı", 0.61),
    ("Çizgi titremesi", 0.59),
    ("Figür eğikliği", 0.56),
]


def draw_fidelity_chart(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int]) -> None:
    x1, y1, x2, y2 = box
    card(draw, box, radius=24, fill="#FFFFFF")
    pad = 50
    draw.text((x1 + pad, y1 + 34), "Gösterge Sadakati (Pearson r)", font=f(46, bold=True), fill=NAVY)
    draw.text(
        (x1 + pad, y1 + 92),
        "Model tahmini ↔ OpenCV ölçümü · ortalama r = 0,79 · 16/16 gösterge r > 0,5",
        font=f(29),
        fill=MUTED,
    )
    top = y1 + 160
    bottom = y2 - 40
    label_w = 540
    bar_x = x1 + pad + label_w
    bar_max = (x2 - pad - 130) - bar_x
    rows = len(FIDELITY_DATA)
    row_h = (bottom - top) // rows
    for i, (label, r) in enumerate(FIDELITY_DATA):
        ry = top + i * row_h
        color = GREEN if r >= 0.70 else BLUE
        draw.text((x1 + pad, ry + (row_h - 30) // 2), label, font=f(28, bold=True), fill=TEXT)
        by = ry + (row_h - 28) // 2
        draw.rounded_rectangle((bar_x, by, bar_x + bar_max, by + 28), radius=14, fill="#EEF2F6")
        draw.rounded_rectangle((bar_x, by, bar_x + int(bar_max * r), by + 28), radius=14, fill=color)
        draw.text((bar_x + bar_max + 20, by - 4), f"{r:.2f}".replace(".", ","), font=f(28, bold=True), fill=NAVY)


def info_tile(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    title: str,
    body: str,
    accent: str,
) -> None:
    x1, y1, x2, y2 = box
    card(draw, box, radius=20, fill="#FFFDF9")
    draw.rounded_rectangle((x1, y1, x1 + 14, y2), radius=7, fill=accent)
    draw_wrapped(draw, title, x1 + 34, y1 + 28, x2 - x1 - 62, f(33, bold=True), fill=NAVY, leading=40)
    draw_wrapped(draw, body, x1 + 34, y1 + 86, x2 - x1 - 62, f(29), fill=MUTED, leading=37)


def make_poster() -> tuple[Path, Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGBA", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Header logos and title
    logo_path = ROOT / "docs" / "extracted_images_latest" / "image1.png"
    logo = Image.open(logo_path).convert("RGBA").resize((560, 560), Image.LANCZOS)
    img.alpha_composite(logo, (210, 245))
    img.alpha_composite(logo, (W - 770, 245))

    title_lines = [
        "CCDDA: ÇOCUK ÇİZİMLERİNDEN",
        "DERİN ÖĞRENME İLE DUYGU",
        "DURUMU ANALİZİ",
    ]
    ty = 265
    for line in title_lines:
        ty = draw_centered(draw, line, W // 2, ty, f(112, bold=True), NAVY) + 28
    draw_centered(draw, "Açıklanabilir Klinik Karar Destek Prototipi", W // 2, ty + 10, f(48), TEXT)
    draw_centered(draw, "Danışman: Doç. Dr. Erkan ÇALIŞKAN", W // 2, 790, f(42), TEXT)
    draw_centered(
        draw,
        "Alper YALÇIN · Niğde Ömer Halisdemir Üniversitesi · Bilgisayar Mühendisliği · TÜBİTAK 2209-A",
        W // 2,
        850,
        f(38),
        TEXT,
    )

    # Metric strip
    mx, my, mw, mh = 260, 955, 844, 180
    metrics = [
        ("5.177", "Elle etiketli KIDO çizimi", LINE),
        ("6.619", "Artırılmış eğitim örneği", BLUE),
        ("16", "Figür-farkında klinik gösterge", ORANGE),
        ("0,834", "Makro F1 · V2_CB1", GREEN),
        ("%82,1", "Temiz test doğruluğu", PURPLE),
    ]
    for i, (value, label, accent) in enumerate(metrics):
        metric_card(draw, (mx + i * (mw + 45), my, mx + i * (mw + 45) + mw, my + mh), value, label, accent)

    # Body columns
    left_x, left_w = 235, 2020
    right_x, right_w = 2705, 2020
    divider_x = W // 2
    body_top, body_bottom = 1255, H - 260
    draw.rounded_rectangle((divider_x - 6, body_top, divider_x + 6, body_bottom), radius=6, fill=LINE)

    # Left column
    y = body_top + 25
    y = section_title(draw, "GİRİŞ", left_x, y)
    intro = (
        "Çocukların duygusal durumları çoğu zaman yalnızca sözel ifadelerle güvenilir biçimde "
        "anlaşılamaz; projektif çizim testleri klinik psikolojide bu boşluğu destekler, ancak "
        "yorumları uzman gerektirir, zaman alır ve özneldir. CCDDA, çocuklara ait el çizimlerinden "
        "dört duygu örüntüsünü (Mutlu, Üzgün, Kızgın, Korku) sınıflandıran ve kararını klinik "
        "göstergeler, Grad-CAM ısı haritası ve metinsel açıklama ile görünür kılan açıklanabilir "
        "bir yapay zeka karar destek sistemidir."
    )
    y = draw_wrapped(draw, intro, left_x, y, left_w, f(42), fill=TEXT, leading=55)
    y += 72

    y = section_title(draw, "AMAÇ", left_x, y)
    goals = [
        "KIDO veri setindeki çocuk çizimlerini dört duygu sınıfı için düzenli ve yeniden üretilebilir bir deney altyapısına dönüştürmek.",
        "ResNet-50 omurgası üzerine kurulan Concept Bottleneck mimarisiyle kararları yorumlanabilir klinik göstergeler üzerinden üretmek.",
        "Modelin yalnızca sınıf etiketi vermesini değil, uzman değerlendirmesini destekleyen görsel ve metinsel açıklama sunmasını sağlamak.",
        "Klinik tanı yerine, psikolog veya klinisyen tarafından yorumlanacak olasılıksal bir destek çıktısı üretmek.",
    ]
    y = bullet_list(draw, goals, left_x, y, left_w, f(39), bullet_color=LINE, leading=51)
    y += 48

    y = section_title(draw, "YÖNTEM", left_x, y)
    method = [
        "Veri hazırlama: 5.177 özgün çizim elle etiketlendi; Kızgın ve Korku sınıfları klinik kompozisyonu bozmayacak artırmalarla dengelendi ve toplam 6.619 eğitim örneği elde edildi.",
        "Ön işleme: Görseller 224×224 boyutuna getirildi, ImageNet istatistikleriyle normalize edildi ve sınıf dengesizliği eğitim aşamasında dikkate alındı.",
        "Model: Dağıtılan nihai model V2_CB1, ResNet-50 ile 16 figür-farkında klinik gösterge tahmin eder; duygu kararı yalnızca bu yorumlanabilir göstergelerden verilir.",
        "Açıklanabilirlik: Grad-CAM görsel odak alanlarını, LLM/kural tabanlı rapor ise öne çıkan göstergelerin klinik yorumunu sunar.",
        "Uygulama: FastAPI servis katmanı, React/Vite web arayüzü ve PyWebView masaüstü kabuğu ile prototip yerel kullanıma hazırlanmıştır.",
    ]
    y = bullet_list(draw, method, left_x, y, left_w, f(37), bullet_color=ORANGE, leading=49)
    y += 36

    note_box = (left_x, y, left_x + left_w, min(body_bottom, y + 360))
    card(draw, note_box, radius=24, fill="#F8FBFB")
    draw.text((note_box[0] + 36, note_box[1] + 30), "KULLANIM SINIRI", font=f(40, bold=True), fill=LINE_DARK)
    draw_wrapped(
        draw,
        "Sistem klinik tanı aracı değildir. Çıktılar olasılıksal araştırma bulgusu olarak ele alınmalı ve nitelikli bir uzman değerlendirmesiyle birlikte yorumlanmalıdır.",
        note_box[0] + 36,
        note_box[1] + 92,
        left_w - 72,
        f(36),
        fill=TEXT,
        leading=47,
    )
    y = note_box[3] + 72

    y = section_title(draw, "KLİNİK GÖSTERGELER", left_x, y)
    indicator_tiles = [
        ("Figür Boyutu & Yerleşimi", "Küçük/büyük figür, merkezden uzaklık, dikey konum ve eğiklik gibi sayfa kullanım örüntüleri izlenir.", LINE),
        ("Çizgi Kalitesi & Baskı", "Çizgi koyuluğu, titreme, baskı değişkenliği ve keskin açı oranı duygusal yük için sayısallaştırılır.", ORANGE),
        ("Gölgeleme & Bütünlük", "Figür içi gölgeleme, parça kopukluğu ve bileşen sayısı kompozisyon bütünlüğünü açıklar.", BLUE),
        ("Renk & Kompozit", "Sıcak renk oranı, koyu ton kullanımı, boş alan ve form bütünlüğü destekleyici sinyal olarak kullanılır.", GREEN),
    ]
    tile_gap = 34
    tile_w = (left_w - tile_gap) // 2
    tile_h = 360
    for i, (title, body, accent) in enumerate(indicator_tiles):
        tx = left_x + (i % 2) * (tile_w + tile_gap)
        ty2 = y + (i // 2) * (tile_h + tile_gap)
        info_tile(draw, (tx, ty2, tx + tile_w, ty2 + tile_h), title, body, accent)
    y += 2 * tile_h + tile_gap + 78

    y = section_title(draw, "PROTOTİP ÇIKTILARI", left_x, y)
    outputs = [
        "Yeniden üretilebilir eğitim ve değerlendirme betikleri",
        "Grad-CAM ısı haritası ve sınıf olasılıkları",
        "LLM/kural tabanlı klinik açıklama raporu",
        "FastAPI servisi, React arayüzü ve PyWebView masaüstü uygulaması",
    ]
    bullet_list(draw, outputs, left_x, y, left_w, f(36), bullet_color=PURPLE, leading=47)

    # Right column visuals
    ry = body_top + 25
    draw_pipeline(draw, (right_x, ry, right_x + right_w, ry + 410))
    draw_wrapped(
        draw,
        "Şekil 1: Çizim girdisinden klinik gösterge darboğazına ve açıklanabilir duygu çıktısına uzanan çalışma akışı.",
        right_x + 20,
        ry + 432,
        right_w - 40,
        f(28, italic=True),
        fill="#8A94A6",
        leading=36,
        align="center",
    )
    ry += 525

    screenshot_box = (right_x, ry, right_x + right_w, ry + 1180)
    card(draw, screenshot_box, radius=24, fill="#FFFFFF")
    rounded_image(
        img,
        ROOT / "docs" / "screenshots" / "new_analysis_result.png",
        (right_x + 26, ry + 26, right_x + right_w - 26, ry + 1090),
        radius=18,
        mode="contain",
    )
    draw_wrapped(
        draw,
        "Şekil 2: Yeniden tasarlanan arayüzde çizim yükleme, duygu tahmini, güven skoru, Grad-CAM ısı haritası ve sınıf olasılıkları bir arada sunulur.",
        right_x + 30,
        ry + 1108,
        right_w - 60,
        f(28, italic=True),
        fill="#8A94A6",
        leading=36,
        align="center",
    )
    ry += 1290

    chart_box = (right_x, ry, right_x + right_w, ry + 1040)
    draw_fidelity_chart(draw, chart_box)
    draw_wrapped(
        draw,
        "Şekil 3: 16 klinik göstergenin model tahminleri ile OpenCV ölçümleri arasındaki ilişki; ortalama r = 0,79.",
        right_x + 30,
        ry + 1055,
        right_w - 60,
        f(28, italic=True),
        fill="#8A94A6",
        leading=36,
        align="center",
    )
    ry += 1160

    # Results section
    ry = section_title(draw, "SONUÇ VE ÇIKTILAR", right_x, ry)
    results_box = (right_x, ry, right_x + right_w, body_bottom)
    card(draw, results_box, radius=24, fill="#FFFFFF")
    inner_x = right_x + 46
    inner_y = ry + 38
    result_points = [
        "Dağıtılan V2_CB1 Concept Bottleneck modeli temiz testte Makro F1=0,834 ve doğruluk=%82,1 elde etti.",
        "En yüksek deneysel skor 18 göstergeli CB1 varyantında Makro F1=0,849 olarak gözlendi; uygulamada 16 göstergeli V2_CB1 çalışmaktadır.",
        "Yorumlanabilir darboğaz yapısı doğruluk kaybı yaratmadan karar yolunu klinik göstergeler üzerinden görünür kıldı.",
        "Üzgün sınıfı en zor sınıf olarak kaldı; bu durum Happy-Sad görsel örtüşmesi ve sınıf içi çeşitlilikle ilişkilendirildi.",
    ]
    inner_y = bullet_list(draw, result_points, inner_x, inner_y, right_w - 92, f(35), bullet_color=GREEN, leading=46)
    inner_y += 20
    inner_y = draw_bar_chart(
        draw,
        inner_x,
        inner_y,
        right_w - 92,
        [
            ("Mutlu / Happy", 0.862, GREEN),
            ("Üzgün / Sad", 0.663, BLUE),
            ("Kızgın / Angry", 0.932, ORANGE),
            ("Korku / Fear", 0.879, PURPLE),
        ],
    )
    inner_y += 34
    inner_y = draw_model_compare(draw, inner_x, inner_y, right_w - 92)
    inner_y += 18

    draw.text((inner_x, inner_y), "Araştırma Kazanımları", font=f(46, bold=True), fill=NAVY)
    inner_y += 72
    grid_gap = 28
    grid_w = (right_w - 92 - grid_gap) // 2
    grid_h = 250
    gains = [
        ("Açıklanabilirlik", "Karar, 16 klinik gösterge ve görsel odak alanlarıyla izlenebilir hale getirildi.", LINE),
        ("Kalibrasyon", "Güven skorları ve düşük güven durumları klinik yorum için ayrı katman olarak ele alındı.", BLUE),
        ("Dağıtım", "Model, API ve masaüstü arayüzüyle uçtan uca prototip haline getirildi.", ORANGE),
        ("Sınırlılık", "Üzgün sınıfı daha düşük F1 verdi; gerçek klinik kullanım için uzman çalışması gerekir.", PURPLE),
    ]
    for i, (title, body, accent) in enumerate(gains):
        gx = inner_x + (i % 2) * (grid_w + grid_gap)
        gy = inner_y + (i // 2) * (grid_h + grid_gap)
        info_tile(draw, (gx, gy, gx + grid_w, gy + grid_h), title, body, accent)

    # Footer
    draw.line((235, H - 185, W - 235, H - 185), fill="#D7DEE8", width=3)
    footer = "CCDDA · Çocuk Çizimlerinde Açıklanabilir Duygu Sınıflandırması · NÖHÜ Bilgisayar Mühendisliği · 2026"
    draw_centered(draw, footer, W // 2, H - 140, f(30), MUTED)

    png_path = OUT_DIR / "ccdda_poster.png"
    preview_path = OUT_DIR / "ccdda_poster_preview.png"
    pdf_path = OUT_DIR / "ccdda_poster.pdf"
    img.convert("RGB").save(png_path, quality=95)
    preview = img.convert("RGB").resize((1240, 1754), Image.LANCZOS)
    preview.save(preview_path, quality=92)
    img.convert("RGB").save(pdf_path, "PDF", resolution=150.0, quality=95)
    return png_path, preview_path, pdf_path


if __name__ == "__main__":
    for path in make_poster():
        print(path)
