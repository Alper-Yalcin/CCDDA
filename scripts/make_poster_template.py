"""CCDDA için temiz, modern, akademik poster ŞABLONU üretir.

Amaç: dolu değil; placeholder'lı, düzenli bir şablon. Tek vurgu rengi turuncu,
nötr/taupe tonlar, serif başlık + modern sans gövde, iyi grid ve hiyerarşi.

Çıktı: out/ccdda_poster_template.{png,pdf} + _preview.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "out"

# ── Tuval (dikey / A1'e yakın, akademik portre) ──────────────────────────────
W, H = 3508, 5560

# ── Palet (yalnızca turuncu vurgu + nötrler) ─────────────────────────────────
BG = "#FAF7F2"        # arka plan
CARD = "#FFFDF9"      # kart / kutu zemini
BORDER = "#E9E1D7"    # ince kenarlık
TEXT = "#1F1F1F"      # birincil metin
TEXT2 = "#555555"     # ikincil metin
ACCENT = "#E76F3C"    # tek vurgu rengi
SOFT = "#FFF1E8"      # yumuşak turuncu zemin
MUTED = "#8A7F73"     # nötr taupe

# ── Yerleşim gridi ───────────────────────────────────────────────────────────
M = 200                      # dış kenar boşluğu
CW = W - 2 * M               # içerik genişliği
GUTTER = 96
LEFT_W = 1300
RIGHT_X = M + LEFT_W + GUTTER
RIGHT_W = CW - LEFT_W - GUTTER

# ── Fontlar ──────────────────────────────────────────────────────────────────
FONTS = Path("C:/Windows/Fonts")
SERIF = str(FONTS / "georgiab.ttf")        # serif başlık
SERIF_REG = str(FONTS / "georgia.ttf")
SANS = str(FONTS / "segoeui.ttf")          # modern sans gövde
SANS_B = str(FONTS / "segoeuib.ttf")
SANS_L = str(FONTS / "segoeuil.ttf")
SANS_I = str(FONTS / "segoeuii.ttf")


def serif(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(SERIF, size)


def serif_reg(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(SERIF_REG, size)


def sans(size: int, weight: str = "r") -> ImageFont.FreeTypeFont:
    path = {"r": SANS, "b": SANS_B, "l": SANS_L, "i": SANS_I}[weight]
    return ImageFont.truetype(path, size)


# ── Yardımcılar ──────────────────────────────────────────────────────────────
def tsize(d: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    l, t, r, b = d.textbbox((0, 0), text, font=font)
    return r - l, b - t


def wrap(d, text, font, max_w) -> list[str]:
    out, cur = [], ""
    for word in text.split():
        trial = word if not cur else f"{cur} {word}"
        if tsize(d, trial, font)[0] <= max_w:
            cur = trial
        else:
            if cur:
                out.append(cur)
            cur = word
    if cur:
        out.append(cur)
    return out


def para(d, text, x, y, max_w, font, fill=TEXT, leading=None, align="left") -> int:
    if leading is None:
        leading = int(font.size * 1.42)
    for line in wrap(d, text, font, max_w):
        w, _ = tsize(d, line, font)
        dx = 0 if align == "left" else (max_w - w) // 2 if align == "center" else max_w - w
        d.text((x + dx, y), line, font=font, fill=fill)
        y += leading
    return y


def centered(d, text, cx, y, font, fill) -> int:
    w, h = tsize(d, text, font)
    d.text((cx - w // 2, y), text, font=font, fill=fill)
    return y + h


def tracked(d, text, x, y, font, fill, spacing=8) -> None:
    """Harf aralıklı (letter-spacing) küçük etiket."""
    cx = x
    for ch in text:
        d.text((cx, y), ch, font=font, fill=fill)
        cx += tsize(d, ch, font)[0] + spacing


def section_title(d, text, x, y, max_w=None) -> int:
    font = serif(74)
    d.text((x, y), text, font=font, fill=TEXT)
    w, h = tsize(d, text, font)
    d.rounded_rectangle((x, y + h + 22, x + 96, y + h + 34), radius=6, fill=ACCENT)
    return y + h + 70


def hairline(d, x1, y, x2, color=BORDER, width=3) -> None:
    d.line((x1, y, x2, y), fill=color, width=width)


def bullets(d, items, x, y, max_w, font, leading=None, gap=26) -> int:
    if leading is None:
        leading = int(font.size * 1.42)
    for item in items:
        d.ellipse((x + 4, y + 16, x + 20, y + 32), fill=ACCENT)
        y = para(d, item, x + 50, y, max_w - 50, font, fill=TEXT2, leading=leading)
        y += gap
    return y


def dashed_rrect(d, box, radius, color, width=3, dash=26, space=20) -> None:
    x1, y1, x2, y2 = box

    def h_dashes(y):
        cx = x1 + radius
        while cx < x2 - radius:
            d.line((cx, y, min(cx + dash, x2 - radius), y), fill=color, width=width)
            cx += dash + space

    def v_dashes(x):
        cy = y1 + radius
        while cy < y2 - radius:
            d.line((x, cy, x, min(cy + dash, y2 - radius)), fill=color, width=width)
            cy += dash + space

    h_dashes(y1)
    h_dashes(y2)
    v_dashes(x1)
    v_dashes(x2)
    d.arc((x1, y1, x1 + 2 * radius, y1 + 2 * radius), 180, 270, fill=color, width=width)
    d.arc((x2 - 2 * radius, y1, x2, y1 + 2 * radius), 270, 360, fill=color, width=width)
    d.arc((x1, y2 - 2 * radius, x1 + 2 * radius, y2), 90, 180, fill=color, width=width)
    d.arc((x2 - 2 * radius, y2 - 2 * radius, x2, y2), 0, 90, fill=color, width=width)


def image_placeholder(d, box, title, note) -> None:
    """Başlık (kutu üstünde) + içi placeholder olan görsel alanı."""
    x1, y1, x2, y2 = box
    # Başlık
    d.text((x1, y1), title, font=sans(40, "b"), fill=TEXT)
    bw, bh = tsize(d, title, sans(40, "b"))
    top = y1 + bh + 24
    # Kutu
    d.rounded_rectangle((x1, top, x2, y2), radius=22, fill=CARD)
    dashed_rrect(d, (x1, top, x2, y2), 22, BORDER, width=3)
    cx, cy = (x1 + x2) // 2, (top + y2) // 2
    # Basit görsel ikonu (dağ + güneş)
    glyph(d, "image", cx, cy - 34, ACCENT, s=46, w=6)
    centered(d, note, cx, cy + 40, sans(33, "i"), MUTED)


def info_block(d, box, title, note, big_number=None) -> None:
    """Küçük, sade bilgi bloğu (klinik gösterge grupları için)."""
    x1, y1, x2, y2 = box
    d.rounded_rectangle(box, radius=20, fill=CARD, outline=BORDER, width=2)
    d.rounded_rectangle((x1, y1, x1 + 12, y2), radius=6, fill=ACCENT)
    d.text((x1 + 40, y1 + 30), title, font=sans(38, "b"), fill=TEXT)
    para(d, note, x1 + 40, y1 + 92, x2 - x1 - 76, sans(31, "i"), fill=MUTED, leading=42)


# ── İkonlar (sade, tutarlı çizgi) ────────────────────────────────────────────
def glyph(d, kind, cx, cy, color, s=34, w=7) -> None:
    if kind == "pencil":
        d.line((cx - s * 0.8, cy + s * 0.8, cx + s * 0.35, cy - s * 0.65), fill=color, width=w)
        d.polygon([(cx + s * 0.35, cy - s * 0.65), (cx + s * 0.75, cy - s * 0.5),
                   (cx + s * 0.55, cy - s * 0.95)], fill=color)
        d.line((cx - s * 0.8, cy + s * 0.8, cx - s * 0.55, cy + s * 0.9), fill=color, width=w)
    elif kind == "crop":
        d.rectangle((cx - s, cy - s * 0.75, cx + s, cy + s * 0.75), outline=color, width=w)
        for dx in (-1, 1):
            for dy in (-1, 1):
                d.line((cx + dx * s * 0.55, cy + dy * s * 0.4, cx + dx * s, cy + dy * s * 0.4), fill=color, width=w)
    elif kind == "layers":
        for i, dy in enumerate((-s * 0.55, 0, s * 0.55)):
            d.polygon([(cx, cy + dy - s * 0.45), (cx + s, cy + dy), (cx, cy + dy + s * 0.45),
                       (cx - s, cy + dy)], outline=color, width=max(4, w - 2))
    elif kind == "checklist":
        for dy in (-s * 0.6, 0, s * 0.6):
            d.ellipse((cx - s, cy + dy - 7, cx - s + 14, cy + dy + 7), fill=color)
            d.line((cx - s * 0.5, cy + dy, cx + s, cy + dy), fill=color, width=w)
    elif kind == "funnel":
        d.polygon([(cx - s, cy - s * 0.7), (cx + s, cy - s * 0.7), (cx + s * 0.25, cy + s * 0.15),
                   (cx - s * 0.25, cy + s * 0.15)], outline=color, width=w)
        d.line((cx, cy + s * 0.15, cx, cy + s * 0.85), fill=color, width=w)
    elif kind == "smile":
        d.ellipse((cx - s, cy - s, cx + s, cy + s), outline=color, width=w)
        d.ellipse((cx - s * 0.45 - 6, cy - s * 0.3 - 6, cx - s * 0.45 + 6, cy - s * 0.3 + 6), fill=color)
        d.ellipse((cx + s * 0.45 - 6, cy - s * 0.3 - 6, cx + s * 0.45 + 6, cy - s * 0.3 + 6), fill=color)
        d.arc((cx - s * 0.55, cy - s * 0.2, cx + s * 0.55, cy + s * 0.6), 20, 160, fill=color, width=w)
    elif kind == "heat":
        for rr in (s, s * 0.66, s * 0.33):
            d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=color, width=max(4, w - 2))
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=color)
    elif kind == "chat":
        d.rounded_rectangle((cx - s, cy - s * 0.8, cx + s, cy + s * 0.45), radius=14, outline=color, width=w)
        d.polygon([(cx - s * 0.4, cy + s * 0.45), (cx - s * 0.05, cy + s * 0.45), (cx - s * 0.45, cy + s * 0.95)], fill=color)
        d.line((cx - s * 0.55, cy - s * 0.2, cx + s * 0.55, cy - s * 0.2), fill=color, width=max(4, w - 2))
    elif kind == "doc":
        d.rounded_rectangle((cx - s * 0.75, cy - s, cx + s * 0.75, cy + s), radius=10, outline=color, width=w)
        for dy in (-s * 0.4, 0, s * 0.4):
            d.line((cx - s * 0.4, cy + dy, cx + s * 0.4, cy + dy), fill=color, width=max(4, w - 2))
    elif kind == "image":
        d.rounded_rectangle((cx - s, cy - s * 0.78, cx + s, cy + s * 0.78), radius=12, outline=color, width=w)
        d.ellipse((cx - s * 0.55, cy - s * 0.45, cx - s * 0.2, cy - s * 0.1), outline=color, width=max(4, w - 2))
        d.line((cx - s * 0.8, cy + s * 0.55, cx - s * 0.15, cy - s * 0.1, cx + s * 0.25, cy + s * 0.25,
                cx + s * 0.8, cy - s * 0.3), fill=color, width=max(4, w - 2), joint="curve")


# ── Akış şeması (dikey, 9 adım) ──────────────────────────────────────────────
FLOW_STEPS = [
    ("pencil", "Çizim Girdisi"),
    ("crop", "Ön İşleme"),
    ("layers", "ResNet-50 Özellik Çıkarımı"),
    ("checklist", "16 Klinik Gösterge Tahmini"),
    ("funnel", "Concept Bottleneck"),
    ("smile", "Duygu Sınıflandırması"),
    ("heat", "Grad-CAM Açıklama"),
    ("chat", "LLM Klinik Açıklama"),
    ("doc", "Sonuç / Rapor Çıktısı"),
]


def draw_flow(d, x, y, w) -> int:
    card_h = 150
    gap = 46
    badge_r = 50
    for i, (kind, title) in enumerate(FLOW_STEPS):
        top = y + i * (card_h + gap)
        box = (x, top, x + w, top + card_h)
        d.rounded_rectangle(box, radius=20, fill=CARD, outline=BORDER, width=2)
        cy = top + card_h // 2
        bx = x + 90
        d.ellipse((bx - badge_r, cy - badge_r, bx + badge_r, cy + badge_r), fill=SOFT)
        glyph(d, kind, bx, cy, ACCENT, s=34, w=7)
        d.text((x + 190, cy - tsize(d, title, sans(44, "b"))[1] // 2 - 4), title, font=sans(44, "b"), fill=TEXT)
        # zarif soluk adım numarası
        num = f"{i + 1:02d}"
        nw, nh = tsize(d, num, serif(70))
        d.text((x + w - nw - 44, cy - nh // 2 - 8), num, font=serif(70), fill=BORDER)
        # bağlayıcı ok
        if i < len(FLOW_STEPS) - 1:
            ax = x + w // 2
            ay1 = top + card_h + 8
            ay2 = top + card_h + gap - 8
            d.line((ax, ay1, ax, ay2 - 6), fill=MUTED, width=4)
            d.polygon([(ax - 13, ay2 - 16), (ax + 13, ay2 - 16), (ax, ay2)], fill=ACCENT)
    return y + len(FLOW_STEPS) * (card_h + gap) - gap


# ── Poster ───────────────────────────────────────────────────────────────────
def make() -> tuple[Path, Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # ===== ÜST BAŞLIK ALANI =====
    head_top = M
    # küçük üst etiket (ortalı)
    label = "LİSANS TEZİ · ARAŞTIRMA PROJESİ"
    lw = sum(tsize(d, ch, sans(34, "b"))[0] + 10 for ch in label) - 10
    tracked(d, label, W // 2 - lw // 2, head_top, sans(34, "b"), ACCENT, spacing=10)

    # logo placeholder'ları (sol & sağ üst)
    logo_w, logo_h = 360, 300
    logo_y = head_top + 70
    for lx, txt in ((M, "[ Üniversite\nlogosu ]"), (W - M - logo_w, "[ Proje / destek\nlogosu ]")):
        dashed_rrect(d, (lx, logo_y, lx + logo_w, logo_y + logo_h), 20, BORDER, width=3)
        lines = txt.split("\n")
        ly = logo_y + logo_h // 2 - len(lines) * 24
        for ln in lines:
            centered(d, ln.strip(), lx + logo_w // 2, ly, sans(32, "i"), MUTED)
            ly += 50

    # büyük başlık (logolar arası ortalı, 2 satır)
    title_max = W - 2 * (M + logo_w + 70)
    title_font = serif(108)
    title_lines = wrap(d, "CCDDA: Çocuk Çizimlerinden Derin Öğrenme ile Duygu Durumu Analizi", title_font, title_max)
    ty = head_top + 96
    for ln in title_lines:
        ty = centered(d, ln, W // 2, ty, title_font, TEXT) + 24
    ty += 8
    ty = centered(d, "Açıklanabilir Klinik Karar Destek Prototipi", W // 2, ty, serif_reg(54), ACCENT) + 34
    info = "Niğde Ömer Halisdemir Üniversitesi · Bilgisayar Mühendisliği Bölümü · TÜBİTAK 2209-A"
    ty = centered(d, info, W // 2, ty, sans(40), TEXT2) + 14
    ty = centered(d, "Danışman: Doç. Dr. Erkan ÇALIŞKAN     ·     Öğrenci: Alper YALÇIN", W // 2, ty, sans(40), TEXT2) + 10

    head_bottom = max(ty + 30, logo_y + logo_h + 30)
    hairline(d, M, head_bottom, W - M, BORDER, 3)

    # ===== METRİK ŞERİDİ (premium bilgi blokları) =====
    ms_top = head_bottom + 56
    ms_h = 290
    d.rounded_rectangle((M, ms_top, M + CW, ms_top + ms_h), radius=26, fill=CARD, outline=BORDER, width=2)
    metrics = [
        ("5.177", "KIDO çizimi"),
        ("16", "Klinik gösterge"),
        ("0,834", "Makro F1"),
        ("%82,1", "Test doğruluğu"),
        ("r = 0,79", "Gösterge sadakati"),
    ]
    cell = CW / len(metrics)
    for i, (val, lab) in enumerate(metrics):
        cx = int(M + cell * i + cell / 2)
        if i > 0:
            dx = int(M + cell * i)
            d.line((dx, ms_top + 54, dx, ms_top + ms_h - 54), fill=BORDER, width=2)
        centered(d, val, cx, ms_top + 70, serif(104), TEXT)
        centered(d, lab, cx, ms_top + 196, sans(38), MUTED)

    # ===== GÖVDE: İKİ KOLON =====
    body_top = ms_top + ms_h + 90

    # —— SOL KOLON —— Giriş / Amaç / Yöntem / Kullanım Sınırı
    ly = body_top
    ly = section_title(d, "Giriş", M, ly)
    ly = para(d, "[ Bu alana çocuk çizimlerinden duygu analizi problemini, neden önemli "
                 "olduğunu ve açıklanabilirliğin klinik değerini anlatan kısa giriş metni "
                 "gelecek. ]", M, ly, LEFT_W, sans(40), fill=TEXT2, leading=58)
    ly += 64

    ly = section_title(d, "Amaç", M, ly)
    ly = bullets(d, ["[ Amaç maddesi 1 ]", "[ Amaç maddesi 2 ]", "[ Amaç maddesi 3 ]",
                     "[ Amaç maddesi 4 ]"], M, ly, LEFT_W, sans(40))
    ly += 40

    ly = section_title(d, "Yöntem", M, ly)
    ly = bullets(d, ["[ Veri hazırlama açıklaması buraya gelecek ]",
                     "[ Model eğitimi açıklaması buraya gelecek ]",
                     "[ Klinik gösterge tahmini açıklaması buraya gelecek ]",
                     "[ Grad-CAM / açıklanabilirlik açıklaması buraya gelecek ]",
                     "[ LLM açıklama / raporlama açıklaması buraya gelecek ]"],
                  M, ly, LEFT_W, sans(40))
    ly += 50

    # Kullanım sınırı kutusu (hafif vurgulu)
    note_h = 280
    note_box = (M, ly, M + LEFT_W, ly + note_h)
    d.rounded_rectangle(note_box, radius=22, fill=SOFT, outline="#F3C9B0", width=2)
    d.rounded_rectangle((M, ly, M + 14, ly + note_h), radius=7, fill=ACCENT)
    d.text((M + 46, ly + 34), "Kullanım Sınırı", font=sans(42, "b"), fill="#9A3B17")
    para(d, "[ Bu sistem klinik tanı aracı değildir. Uzman değerlendirmesini destekleyen, "
            "açıklanabilir bir araştırma prototipidir. ]",
         M + 46, ly + 108, LEFT_W - 92, sans(36), fill="#7A4B36", leading=50)
    left_bottom = ly + note_h

    # —— SAĞ KOLON —— Sistem Akışı (akış şeması)
    ry = body_top
    ry = section_title(d, "Sistem Akışı", RIGHT_X, ry)
    flow_bottom = draw_flow(d, RIGHT_X, ry, RIGHT_W)

    body_bottom = max(left_bottom, flow_bottom)
    sep_y = body_bottom + 80
    hairline(d, M, sep_y, W - M, BORDER, 3)

    # ===== GÖRSEL ALANLARI (tam genişlik, 4 placeholder) =====
    gy = sep_y + 70
    gy = section_title(d, "Görsel Alanları", M, gy)
    img_titles = [
        ("Örnek Çocuk Çizimi", "[ Buraya örnek çocuk çizimi görseli gelecek ]"),
        ("Grad-CAM Isı Haritası", "[ Buraya Grad-CAM görselleştirmesi gelecek ]"),
        ("Prototip Arayüzü / Analiz Ekranı", "[ Buraya sistem arayüzü ekran görüntüsü gelecek ]"),
        ("Klinik Gösterge Çıktıları", "[ Buraya klinik gösterge tablosu / ekranı gelecek ]"),
    ]
    cols = 4
    gap = 56
    bw = (CW - (cols - 1) * gap) // cols
    box_h = 620
    for i, (title, note) in enumerate(img_titles):
        bx = M + i * (bw + gap)
        image_placeholder(d, (bx, gy, bx + bw, gy + box_h), title, note)
    images_bottom = gy + box_h
    sep2 = images_bottom + 80
    hairline(d, M, sep2, W - M, BORDER, 3)

    # ===== ALT BÖLÜM =====
    # Klinik Göstergeler (4 grup)
    cy0 = sep2 + 70
    cy0 = section_title(d, "Klinik Göstergeler", M, cy0)
    groups = [
        ("Figür Boyutu & Yerleşimi", "[ Açıklama buraya gelecek ]"),
        ("Çizgi Kalitesi & Baskı", "[ Açıklama buraya gelecek ]"),
        ("Gölgeleme & Bütünlük", "[ Açıklama buraya gelecek ]"),
        ("Renk & Kompozit", "[ Açıklama buraya gelecek ]"),
    ]
    gbw = (CW - 3 * gap) // 4
    gbh = 280
    for i, (title, note) in enumerate(groups):
        bx = M + i * (gbw + gap)
        info_block(d, (bx, cy0, bx + gbw, cy0 + gbh), title, note)
    groups_bottom = cy0 + gbh

    # Sonuç ve Çıktılar  |  Nihai Sonuçlar (yan yana)
    col_gap = 96
    half = (CW - col_gap) // 2
    rx2 = M + half + col_gap
    by = groups_bottom + 80

    # Sol: Sonuç ve Çıktılar
    sy = section_title(d, "Sonuç ve Çıktılar", M, by)
    bullets(d, ["[ Sonuç maddesi 1 ]", "[ Sonuç maddesi 2 ]", "[ Sonuç maddesi 3 ]",
                "[ Sonuç maddesi 4 ]", "[ Sonuç maddesi 5 ]"], M, sy, half, sans(40))

    # Sağ: Nihai Sonuçlar (sade barlar, tek vurgu rengi)
    ny = section_title(d, "Nihai Sonuçlar", rx2, by)
    perf = [
        ("Makro F1", 0.834, "0,834"),
        ("Test Doğruluğu", 0.821, "%82,1"),
        ("Gösterge Sadakati", 0.79, "r = 0,79"),
        ("ECE / Kalibrasyon", 0.92, "düşük"),
    ]
    label_w = 470
    bar_x = rx2 + label_w
    bar_max = (M + CW) - bar_x - 230
    for i, (lab, frac, val) in enumerate(perf):
        yy = ny + i * 84
        d.text((rx2, yy + 4), lab, font=sans(36, "b"), fill=TEXT)
        d.rounded_rectangle((bar_x, yy + 10, bar_x + bar_max, yy + 44), radius=17, fill="#EFE7DD")
        d.rounded_rectangle((bar_x, yy + 10, bar_x + int(bar_max * frac), yy + 44), radius=17, fill=ACCENT)
        d.text((bar_x + bar_max + 24, yy), val, font=sans(36, "b"), fill=TEXT)
    cmp_y = ny + len(perf) * 84 + 28
    d.text((rx2, cmp_y), "Model Karşılaştırması", font=sans(38, "b"), fill=TEXT)
    cmp_y += 64
    compare = [("ResNet-50", 0.62), ("ResNet-50 + Klinik", 0.60), ("Kavram Darboğazı", 0.70)]
    label_w2 = 520
    bar_x2 = rx2 + label_w2
    bar_max2 = (M + CW) - bar_x2 - 70
    for i, (lab, frac) in enumerate(compare):
        yy = cmp_y + i * 74
        d.text((rx2, yy + 2), lab, font=sans(34), fill=TEXT2)
        col = ACCENT if "Darboğaz" in lab else MUTED
        d.rounded_rectangle((bar_x2, yy + 8, bar_x2 + bar_max2, yy + 40), radius=16, fill="#EFE7DD")
        d.rounded_rectangle((bar_x2, yy + 8, bar_x2 + int(bar_max2 * frac), yy + 40), radius=16, fill=col)

    # ===== ALT BİLGİ =====
    foot_y = H - 130
    hairline(d, M, foot_y, W - M, BORDER, 3)
    centered(d, "CCDDA · Çocuk Çizimlerinden Açıklanabilir Duygu Analizi · Lisans Tezi · 2026",
             W // 2, foot_y + 34, sans(32), MUTED)

    png = OUT_DIR / "ccdda_poster_template.png"
    pdf = OUT_DIR / "ccdda_poster_template.pdf"
    prev = OUT_DIR / "ccdda_poster_template_preview.png"
    img.save(png)
    img.save(pdf, "PDF", resolution=150.0)
    preview = img.resize((1240, int(1240 * H / W)), Image.LANCZOS)
    preview.save(prev)
    return png, pdf, prev


if __name__ == "__main__":
    for p in make():
        print(p)
