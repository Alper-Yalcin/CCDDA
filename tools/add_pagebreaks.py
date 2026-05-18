"""Tüm ana ön sayfa bölümleri arasına explicit page break ekle.
Her bölüm kendi sayfasında başlasın."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCX = r'c:\Users\alper\Desktop\CCDDA\ÇocukÇizimlerindenDuyduDurumuAnalizi.docx'

# Page break eklenecek bölümler (ön sayfaların her biri yeni sayfada)
PAGE_BREAK_BEFORE = [
    "SUMMARY",
    "İÇİNDEKİLER",
    "ÇİZELGELER DİZİNİ",
    "ŞEKİLLER DİZİNİ",
    "FOTOĞRAFLAR DİZİNİ",
    "SİMGE VE KISALTMALAR",
    # ÖN SÖZ zaten önceki adımda eklendi
]


def has_page_break_in_paragraph(p):
    """Paragrafın ilk run'ında w:br type=page var mı?"""
    for r in p.runs:
        for br in r._element.findall(qn('w:br')):
            if br.get(qn('w:type')) == 'page':
                return True
    return False


def add_page_break_to_paragraph(p):
    """Paragrafın başına w:br type=page ekle (pPr'den sonra)."""
    new_r = OxmlElement('w:r')
    new_br = OxmlElement('w:br')
    new_br.set(qn('w:type'), 'page')
    new_r.append(new_br)
    pPr = p._element.find(qn('w:pPr'))
    if pPr is not None:
        pPr.addnext(new_r)
    else:
        p._element.insert(0, new_r)


doc = docx.Document(DOCX)

for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    # tab karakteri ile başlayan İÇİNDEKİLER olabilir
    t_clean = t.lstrip('\t').strip()
    if t_clean in PAGE_BREAK_BEFORE:
        if has_page_break_in_paragraph(p):
            print(f"  p{i}: {t_clean} - zaten page break var, atlandı")
            continue
        add_page_break_to_paragraph(p)
        print(f"✓ p{i}: {t_clean} - page break eklendi")

doc.save(DOCX)
print("\nTüm ön sayfa bölümleri kendi sayfalarında başlayacak.")
