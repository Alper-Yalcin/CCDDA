"""CCDDA — KLASİK akademik poster (referans posterle BİREBİR aynı yerleşim).

Referans düzeni: beyaz zemin, üstte ortalanmış büyük başlık, iki yanda NÖHÜ logosu,
başlık altında danışman/öğrenci satırı, ortada ince DİKEY ayraç, sol kolon metin
(GİRİŞ/AMAÇ/YÖNTEM), sağ kolon görsel + flowchart + SONUÇ. Koyu lacivert başlıklar,
teal/turkuaz vurgu. Kart/kutu/dashboard/turuncu YOK.

Çıktı: out/ccdda_poster_academic.{png,pdf} + _preview.png
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "out"

# ── Tuval (A1'e yakın, dikey) ────────────────────────────────────────────────
W, H = 3508, 4600

# ── Renkler (sade akademik: beyaz zemin, lacivert başlık, teal vurgu) ─────────
BG = "#FFFFFF"
HEAD = "#15293B"        # koyu lacivert başlık
BODY = "#2B2F33"        # gövde metni
TEAL = "#0090A8"        # logodaki turkuaz/teal vurgu
TEAL_DK = "#0A6E73"
LINE = "#D6D6D6"        # ince ayraç
PH_FILL = "#F5F6F6"     # görsel placeholder zemini
PH_BORDER = "#C7CDCF"
PH_TEXT = "#8C9296"
CAPTION = "#7A8085"

# ── Grid ─────────────────────────────────────────────────────────────────────
M = 170
MID = W // 2
COL_GAP = 64
LX = M
LW = MID - COL_GAP - LX
RX = MID + COL_GAP
RW = (W - M) - RX

# ── Fontlar (klasik sans — Arial) ────────────────────────────────────────────
FD = Path("C:/Windows/Fonts")
F_REG = str(FD / "arial.ttf")
F_BLD = str(FD / "arialbd.ttf")
F_ITA = str(FD / "ariali.ttf")


def fr(s):  # regular
    return ImageFont.truetype(F_REG, s)


def fb(s):  # bold
    return ImageFont.truetype(F_BLD, s)


def fi(s):  # italic
    return ImageFont.truetype(F_ITA, s)


# ── Metin yardımcıları ───────────────────────────────────────────────────────
def tsz(d, t, f):
    l, t0, r, b = d.textbbox((0, 0), t, font=f)
    return r - l, b - t0


def wrap_lines(d, text, f, max_w):
    """Satırları kelime listeleri olarak döndürür (justify için)."""
    lines, cur = [], []
    for word in text.split():
        trial = " ".join(cur + [word])
        if tsz(d, trial, f)[0] <= max_w or not cur:
            cur.append(word)
        else:
            lines.append(cur)
            cur = [word]
    if cur:
        lines.append(cur)
    return lines


def draw_justified(d, text, x, y, max_w, f, fill=BODY, leading=None):
    if leading is None:
        leading = int(f.size * 1.42)
    lines = wrap_lines(d, text, f, max_w)
    for i, words in enumerate(lines):
        last = i == len(lines) - 1
        if last or len(words) == 1:
            d.text((x, y), " ".join(words), font=f, fill=fill)
        else:
            wsum = sum(tsz(d, w, f)[0] for w in words)
            gap = (max_w - wsum) / (len(words) - 1)
            cx = x
            for w in words:
                d.text((cx, y), w, font=f, fill=fill)
                cx += tsz(d, w, f)[0] + gap
        y += leading
    return y


def draw_left(d, text, x, y, max_w, f, fill=BODY, leading=None):
    if leading is None:
        leading = int(f.size * 1.42)
    for words in wrap_lines(d, text, f, max_w):
        d.text((x, y), " ".join(words), font=f, fill=fill)
        y += leading
    return y


def centered(d, t, cx, y, f, fill):
    w, h = tsz(d, t, f)
    d.text((cx - w // 2, y), t, font=f, fill=fill)
    return y + h


def section(d, title, cx, y, col_x, col_w):
    """Ortalı, büyük harf bölüm başlığı + altında ince teal çizgi."""
    f = fb(60)
    centered(d, title, cx, y, f, HEAD)
    h = tsz(d, title, f)[1]
    ry = y + h + 24
    d.line((col_x, ry, col_x + col_w, ry), fill=LINE, width=2)
    d.line((cx - 90, ry, cx + 90, ry), fill=TEAL, width=5)
    return ry + 40


def bullet(d, text, x, y, max_w, f, leading=None):
    if leading is None:
        leading = int(f.size * 1.42)
    d.rectangle((x, y + 14, x + 16, y + 30), fill=TEAL)
    return draw_left(d, text, x + 42, y, max_w - 42, f, fill=BODY, leading=leading)


def lead_item(d, lead, text, x, y, max_w, f_lead, f_body, leading):
    """Kalın baş etiket + ardından gövde (Yöntem maddeleri)."""
    d.text((x, y), lead, font=f_lead, fill=TEAL_DK)
    lw = tsz(d, lead, f_lead)[0]
    # ilk satır lead'in yanından devam eder
    words = text.split()
    first, rest = [], []
    avail_first = max_w - lw - 14
    i = 0
    while i < len(words):
        trial = " ".join(first + [words[i]])
        if tsz(d, trial, f_body)[0] <= avail_first or not first:
            first.append(words[i]); i += 1
        else:
            break
    rest = words[i:]
    d.text((x + lw + 14, y), " ".join(first), font=f_body, fill=BODY)
    y += leading
    if rest:
        y = draw_left(d, " ".join(rest), x, y, max_w, f_body, fill=BODY, leading=leading)
    return y


def image_area(d, box, ph_text=None, base=None, img_path=None):
    x1, y1, x2, y2 = box
    if img_path is not None:
        # Gerçek görseli kutuya sığacak şekilde (contain) yerleştir, çerçeveyi
        # görselin tam etrafına çiz (boş kenarlık bölgesi kalmasın).
        pad = 6
        iw, ih = (x2 - x1) - 2 * pad, (y2 - y1) - 2 * pad
        im = Image.open(img_path).convert("RGB")
        im.thumbnail((iw, ih), Image.LANCZOS)
        ox = x1 + ((x2 - x1) - im.width) // 2
        oy = y1 + ((y2 - y1) - im.height) // 2
        base.paste(im, (ox, oy))
        d.rectangle((ox - 2, oy - 2, ox + im.width + 1, oy + im.height + 1), outline=PH_BORDER, width=2)
        return
    # Placeholder
    d.rectangle(box, fill=PH_FILL, outline=PH_BORDER, width=2)
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    s = 64
    d.rectangle((cx - s, cy - s * 0.7 - 30, cx + s, cy + s * 0.7 - 30), outline=PH_BORDER, width=4)
    d.ellipse((cx - s * 0.5, cy - s * 0.4 - 30, cx - s * 0.16, cy - 30 - s * 0.06), outline=PH_BORDER, width=4)
    d.line((cx - s * 0.8, cy + s * 0.5 - 30, cx - s * 0.1, cy - 30 - s * 0.1, cx + s * 0.3, cy - 30 + s * 0.2,
            cx + s * 0.8, cy - 30 - s * 0.3), fill=PH_BORDER, width=4, joint="curve")
    for ln_y, ln in enumerate(wrap_lines(d, ph_text, fi(34), x2 - x1 - 120)):
        centered(d, " ".join(ln), cx, cy + 60 + ln_y * 46, fi(34), PH_TEXT)


# ── Akış şeması (yatay serpentin, 8 adım) ────────────────────────────────────
FLOW = [
    "Çizim Girdisi", "Ön İşleme", "ResNet-50 Özellik Çıkarımı", "16 Klinik Gösterge",
    "Concept Bottleneck", "Duygu Tahmini", "Grad-CAM + LLM Açıklama", "Rapor Çıktısı",
]


def flow_box(d, box, text):
    x1, y1, x2, y2 = box
    d.rectangle(box, fill="#FFFFFF", outline=HEAD, width=3)
    d.rectangle((x1, y1, x2, y1 + 9), fill=TEAL)
    f = fb(29)
    lines = wrap_lines(d, text, f, x2 - x1 - 28)
    th = len(lines) * 36
    yy = (y1 + y2) // 2 - th // 2 + 4
    for ln in lines:
        centered(d, " ".join(ln), (x1 + x2) // 2, yy, f, HEAD)
        yy += 36


def arrow(d, x1, y1, x2, y2):
    d.line((x1, y1, x2, y2), fill=TEAL, width=5)
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    L = 22
    for da in (math.pi * 0.85, -math.pi * 0.85):
        d.line((x2, y2, x2 + L * math.cos(ang + da), y2 + L * math.sin(ang + da)), fill=TEAL, width=5)


def draw_flow(d, x, y, w):
    cols = 4
    gap = 60
    bw = (w - (cols - 1) * gap) // cols
    bh = 150
    row_gap = 120
    # satır 1 (sol→sağ): 0,1,2,3
    xs = [x + i * (bw + gap) for i in range(cols)]
    y1 = y
    for i in range(4):
        flow_box(d, (xs[i], y1, xs[i] + bw, y1 + bh), FLOW[i])
        if i < 3:
            arrow(d, xs[i] + bw + 8, y1 + bh // 2, xs[i + 1] - 8, y1 + bh // 2)
    # aşağı ok (3 → 4)
    y2 = y1 + bh + row_gap
    arrow(d, xs[3] + bw // 2, y1 + bh + 8, xs[3] + bw // 2, y2 - 8)
    # satır 2 (sağ→sol): 4@col3, 5@col2, 6@col1, 7@col0
    order = [3, 2, 1, 0]
    for k, col in enumerate(order):
        idx = 4 + k
        flow_box(d, (xs[col], y2, xs[col] + bw, y2 + bh), FLOW[idx])
        if k < 3:
            nxt = order[k + 1]
            arrow(d, xs[col] - 8, y2 + bh // 2, xs[nxt] + bw + 8, y2 + bh // 2)
    return y2 + bh


def perf_line(d, label, value, x, y, f_lab, f_val):
    d.text((x, y), label, font=f_lab, fill=TEAL_DK)
    lw = tsz(d, label, f_lab)[0]
    d.text((x + lw + 12, y), value, font=f_val, fill=BODY)
    return y


def load_logo():
    """NÖHÜ logosundaki siyah zemini şeffaflaştır (beyaz postere otursun)."""
    im = Image.open(ROOT / "docs" / "extracted_images_latest" / "image1.png").convert("RGBA")
    px = im.load()
    for yy in range(im.height):
        for xx in range(im.width):
            r, g, b, a = px[xx, yy]
            if max(r, g, b) < 60:
                px[xx, yy] = (r, g, b, 0)
    return im


def make(out_stem="ccdda_poster_academic", right_logo=None):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # ===== ÜST BAŞLIK + LOGOLAR =====
    lsz = 300
    top = 150
    # Sol: NÖHÜ logosu (orijinal — olduğu gibi kalır)
    left_logo = load_logo().resize((lsz, lsz), Image.LANCZOS)
    img.paste(left_logo, (M, top), left_logo)
    # Sağ: belirtilmişse proje logosu, yoksa yine NÖHÜ
    rl = (right_logo if right_logo is not None else load_logo())
    rl = rl.convert("RGBA")
    # oranı koru, lsz kutusuna sığdır
    rl.thumbnail((lsz, lsz), Image.LANCZOS)
    rx_logo = (W - M - lsz) + (lsz - rl.width) // 2
    ry_logo = top + (lsz - rl.height) // 2
    img.paste(rl, (rx_logo, ry_logo), rl)

    # başlık (iki satır, logolar arasına sığacak şekilde otomatik boyut)
    title_l1 = "CCDDA: ÇOCUK ÇİZİMLERİNDEN"
    title_l2 = "DERİN ÖĞRENME İLE DUYGU DURUMU ANALİZİ"
    center_w = (W - M - lsz - 60) - (M + lsz + 60)
    cx = W // 2
    size = 96
    while size > 60:
        if tsz(d, title_l2, fb(size))[0] <= center_w and tsz(d, title_l1, fb(size))[0] <= center_w:
            break
        size -= 2
    ty = top + 8
    ty = centered(d, title_l1, cx, ty, fb(size), HEAD) + 14
    ty = centered(d, title_l2, cx, ty, fb(size), HEAD) + 26
    ty = centered(d, "Açıklanabilir Klinik Karar Destek Prototipi", cx, ty, fi(50), TEAL_DK) + 30
    ty = centered(d, "Danışman: Doç. Dr. Erkan ÇALIŞKAN", cx, ty, fr(40), BODY) + 12
    ty = centered(d, "Alper YALÇIN · Niğde Ömer Halisdemir Üniversitesi · Bilgisayar Mühendisliği · TÜBİTAK 2209-A",
                  cx, ty, fr(38), BODY) + 8

    head_bottom = max(ty + 26, top + lsz + 26)
    d.line((M, head_bottom, W - M, head_bottom), fill=LINE, width=3)

    # ===== ORTA DİKEY AYRAÇ =====
    col_top = head_bottom + 60
    col_bottom = H - 150
    d.line((MID, col_top + 10, MID, col_bottom - 10), fill=LINE, width=2)

    # ===== SOL KOLON =====
    lcx = LX + LW // 2
    y = col_top
    y = section(d, "GİRİŞ", lcx, y, LX, LW)
    y = draw_justified(
        d,
        "Çocuklar; korku, kaygı, öfke veya mutluluk gibi duygusal ve psikolojik durumlarını çoğu "
        "zaman sözel olarak tam ifade edemez. Bu nedenle çizim, çocuğun iç dünyasına ulaşmada "
        "klinik psikolojide uzun süredir kullanılan önemli bir projektif değerlendirme aracıdır. "
        "Figürlerin boyutu, sayfadaki yerleşimi, çizgi baskısı, renk seçimi ve gölgeleme gibi "
        "ipuçları çocuğun duygu durumu hakkında anlamlı işaretler taşıyabilir. Ancak bu ipuçlarının "
        "yorumlanması uzman bilgisi gerektirir, zaman alıcıdır ve değerlendiriciden değerlendiriciye "
        "değişebilen öznel yargılar içerir.",
        LX, y, LW, fr(42), leading=68,
    )
    y += 28
    y = draw_justified(
        d,
        "Derin öğrenme yöntemleri bu süreci hızlandırma ve standartlaştırma potansiyeli taşır; "
        "fakat yalnızca sınıf etiketi üreten kara kutu modeller klinik bağlamda güven, şeffaflık ve "
        "hesap verebilirlik açısından yetersiz kalır. Bu çalışma, çocuk çizimlerinden duygu durumunu "
        "tahmin ederken kararın hangi klinik göstergelere dayandığını da açıklayabilen açıklanabilir "
        "bir yapay zekâ karar destek yaklaşımı geliştirmeyi hedefler; böylece doğruluk ile "
        "yorumlanabilirliği birlikte gözeten bir tasarım benimsenir.",
        LX, y, LW, fr(42), leading=68,
    )
    y += 70

    y = section(d, "AMAÇ", lcx, y, LX, LW)
    y = draw_justified(
        d,
        "Projenin temel amacı, KIDO veri setindeki çocuk çizimlerinden Mutlu, Üzgün, Kızgın ve "
        "Korku duygu sınıflarını tahmin eden; model kararlarını klinik göstergeler, Grad-CAM ısı "
        "haritaları ve LLM destekli açıklamalarla yorumlanabilir kılan, uzman değerlendirmesine "
        "destek olacak bir karar destek sistemi geliştirmektir. Böylece tahmin sonucunun yanında, "
        "bu sonuca hangi göstergelerin yol açtığı da görünür kılınır.",
        LX, y, LW, fr(42), leading=68,
    )
    y += 32
    for it in [
        "KIDO veri seti üzerinde dört sınıflı duygu sınıflandırması gerçekleştirmek.",
        "ResNet-50 tabanlı bir derin öğrenme modeli geliştirmek.",
        "16 figür-farkında klinik gösterge ile açıklanabilir bir karar yolu oluşturmak.",
        "Grad-CAM ve LLM açıklamaları ile uzman yorumunu desteklemek.",
    ]:
        y = bullet(d, it, LX, y, LW, fr(42), leading=62) + 22
    y += 52

    y = section(d, "YÖNTEM", lcx, y, LX, LW)
    methods = [
        ("Veri Hazırlama:", "5.177 çocuk çizimi elle etiketlendi ve ayrı bir temiz test seti "
                            "ayrıldı; sınıf dengesizliği, kompozisyonu bozmayan veri artırma ve "
                            "224×224 ön işleme ile dengelendi."),
        ("Model Eğitimi:", "EfficientNet, ResNet-50, MobileNetV3 ve ViT omurgaları karşılaştırıldı; "
                           "doğruluk ve kararlılık açısından en dengeli sonucu veren ResNet-50 nihai "
                           "omurga olarak seçildi."),
        ("Kavram Darboğazı:", "ResNet-50 görüntüden 16 figür-farkında klinik gösterge tahmin eder; "
                              "duygu kararı doğrudan pikselden değil yalnızca bu yorumlanabilir "
                              "göstergeler üzerinden verilir."),
        ("Açıklanabilirlik:", "Grad-CAM ısı haritaları modelin odaklandığı çizim bölgelerini, LLM "
                              "destekli modül ise öne çıkan göstergelerin klinik yorumunu üretir."),
        ("Prototip:", "FastAPI servis katmanı, React/Vite web arayüzü ve masaüstü/web istemcisiyle "
                      "uçtan uca çalışan bir analiz prototipi sunulur."),
    ]
    for lead, txt in methods:
        y = lead_item(d, lead, txt, LX, y, LW, fb(42), fr(42), leading=64) + 30

    y += 28
    d.text((LX, y), "KULLANIM SINIRI", font=fb(42), fill=TEAL_DK)
    y += 62
    y = draw_justified(
        d,
        "Bu sistem klinik tanı aracı değildir. Çıktılar, uzman değerlendirmesine destek amacıyla "
        "sunulan olasılıksal araştırma sonuçlarıdır.",
        LX, y, LW, fi(40), fill=BODY, leading=56,
    )

    # ===== SAĞ KOLON =====
    rcx = RX + RW // 2
    y = col_top
    y = section(d, "SİSTEM AKIŞI", rcx, y, RX, RW)
    fb_y = draw_flow(d, RX, y, RW)
    y = fb_y + 28
    y = centered(
        d,
        "Şekil 1: CCDDA sistem akışı — çizim girdisinden açıklanabilir duygu raporuna.",
        rcx, y, fi(32), CAPTION,
    ) + 64
    y_imgs = y

    cap2 = ("Şekil 2: Geliştirilen arayüzde çocuk çizimi, duygu tahmini, güven skoru, Grad-CAM ısı "
            "haritası ve klinik açıklama birlikte sunulur.")
    cap3 = ("Şekil 3: Modelin tahmin kararını etkileyen bölgeler Grad-CAM ısı haritası ile "
            "görselleştirilir.")
    sonuc_items = [
        "Kavram Darboğazı modeli temiz test setinde Makro F1 = 0,834 ve doğruluk = %82,1 değerlerine ulaşmıştır.",
        "Model, duygu kararını doğrudan piksellerden değil 16 figür-farkında klinik gösterge üzerinden üretir.",
        "Grad-CAM görselleştirmesi modelin odaklandığı çizim bölgelerini görünür kılar.",
        "LLM destekli açıklama modülü tahmini uzman dostu metinlerle destekler.",
        "Sistem klinik tanı aracı değil, uzman değerlendirmesine destek olan açıklanabilir bir prototiptir.",
    ]

    # Gerçek görseller — kutu yüksekliği görselin tam genişlikteki doğal yüksekliği
    img1_path = ROOT / "docs" / "screenshots" / "new_analysis_result.png"
    img2_path = ROOT / "docs" / "screenshots" / "ornek_cizim_gradcam.png"
    title_h = 58

    def natural_h(path):
        im = Image.open(path)
        return round(RW * im.height / im.width)

    box1_h = natural_h(img1_path)
    box2_h = natural_h(img2_path)

    # Görsel Alanı 1
    d.text((RX, y), "GÖRSEL ALANI 1: ANALİZ ARAYÜZÜ", font=fb(38), fill=HEAD)
    y += title_h
    image_area(d, (RX, y, RX + RW, y + box1_h), base=img, img_path=img1_path)
    y += box1_h + 22
    y = draw_left(d, cap2, RX, y, RW, fi(32), fill=CAPTION, leading=44) + 46

    # Görsel Alanı 2
    d.text((RX, y), "GÖRSEL ALANI 2: ÖRNEK ÇİZİM + GRAD-CAM", font=fb(38), fill=HEAD)
    y += title_h
    image_area(d, (RX, y, RX + RW, y + box2_h), base=img, img_path=img2_path)
    y += box2_h + 22
    y = draw_left(d, cap3, RX, y, RW, fi(32), fill=CAPTION, leading=44) + 56

    # SONUÇ
    y = section(d, "SONUÇ", rcx, y, RX, RW)
    for it in sonuc_items:
        y = bullet(d, it, RX, y, RW, fr(37), leading=50) + 16
    y += 24
    d.line((RX, y, RX + RW, y), fill=LINE, width=2)
    y += 34
    f_lab, f_val = fb(36), fr(36)
    rows = [
        ("Nihai Model: ", "Kavram Darboğazı", "Makro F1: ", "0,834"),
        ("Test Doğruluğu: ", "%82,1", "Gösterge Sadakati: ", "r = 0,79"),
        ("ECE (Kalibrasyon): ", "0,019", "", ""),
    ]
    col2_x = RX + RW // 2 + 20
    for lab1, val1, lab2, val2 in rows:
        perf_line(d, lab1, val1, RX, y, f_lab, f_val)
        if lab2:
            perf_line(d, lab2, val2, col2_x, y, f_lab, f_val)
        y += 56

    # ===== ALT BİLGİ =====
    foot_y = H - 110
    d.line((M, foot_y, W - M, foot_y), fill=LINE, width=2)
    centered(d, "CCDDA · Çocuk Çizimlerinden Açıklanabilir Duygu Analizi · Lisans Tezi · 2026",
             W // 2, foot_y + 30, fr(30), CAPTION)

    png = OUT_DIR / f"{out_stem}.png"
    pdf = OUT_DIR / f"{out_stem}.pdf"
    prev = OUT_DIR / f"{out_stem}_preview.png"
    img.save(png)
    img.save(pdf, "PDF", resolution=150.0)
    img.resize((1240, int(1240 * H / W)), Image.LANCZOS).save(prev)
    return png, pdf, prev


def render(out_stem, accent, accent_dk, head, right_logo):
    """Tema renklerini (global) ayarlayıp posteri üretir."""
    global TEAL, TEAL_DK, HEAD
    TEAL, TEAL_DK, HEAD = accent, accent_dk, head
    return make(out_stem, right_logo)


if __name__ == "__main__":
    # 1) Orijinal akademik sürüm — NÖHÜ teal, iki yanda NÖHÜ logosu
    for p in render("ccdda_poster_academic", "#0090A8", "#0A6E73", "#15293B", None):
        print(p)
    # 2) Proje sürümü — sol NÖHÜ (olduğu gibi), sağ proje logosu, vurgu projemizin turuncusu
    proj_logo = Image.open(ROOT / "docs" / "extracted_images_latest" / "project_logo.png").convert("RGBA")
    for p in render("ccdda_poster_academic_proje", "#E76F3C", "#C0532A", "#1F1F1F", proj_logo):
        print(p)
