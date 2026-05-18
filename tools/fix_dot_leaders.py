"""TOC hyperlink yapısını yeniden inşa et: tab ve sayfa numarası hyperlink DIŞINDA olmalı.
Böylece Word dot leader'ı doğru render eder."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import docx
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

DOCX = r'c:\Users\alper\Desktop\CCDDA\docs\ÇocukÇizimlerindenDuyduDurumuAnalizi.docx'


def restructure_toc_paragraph(p):
    """Paragrafta hyperlink yapısını yeniden inşa et: text in hyperlink, tab+page outside."""
    p_elem = p._element

    # Mevcut hyperlink elementini bul
    hyperlink = p_elem.find(qn('w:hyperlink'))
    if hyperlink is None:
        return False

    anchor = hyperlink.get(qn('w:anchor'))
    if not anchor:
        return False

    # Hyperlink içindeki text, tab, page'i ayır
    runs = hyperlink.findall(qn('w:r'))
    if not runs:
        return False

    # 1. run = text (başlık)
    # 2. run = tab
    # 3. run = page number
    title_text = ''
    page_text = ''
    for r in runs:
        for t_el in r.findall(qn('w:t')):
            text = t_el.text or ''
            if title_text == '' and text != '\t':
                title_text = text
            elif page_text == '':
                page_text = text

    if not title_text or not page_text:
        # Belki tek bir run içinde tüm içerik
        full = ''
        for r in runs:
            for t_el in r.findall(qn('w:t')):
                full += t_el.text or ''
            for tab_el in r.findall(qn('w:tab')):
                full += '\t'
        if '\t' in full:
            title_text, page_text = full.split('\t', 1)

    if not title_text:
        return False

    # Yeni yapı:
    # <w:hyperlink>
    #   <w:r>title_text</w:r>
    # </w:hyperlink>
    # <w:r><w:tab/></w:r>
    # <w:r>page_text</w:r>

    # Mevcut hyperlink'in run'larını temizle
    for r in list(hyperlink.findall(qn('w:r'))):
        hyperlink.remove(r)

    # Hyperlink içine sadece text run'ı ekle (siyah, no underline)
    title_r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    color = OxmlElement('w:color')
    color.set(qn('w:val'), '000000')
    rPr.append(color)
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'none')
    rPr.append(u)
    title_r.append(rPr)
    t_el = OxmlElement('w:t')
    t_el.text = title_text
    t_el.set(qn('xml:space'), 'preserve')
    title_r.append(t_el)
    hyperlink.append(title_r)

    # Hyperlink'in HEMEN ARDINA tab run'ı ekle (paragraf seviyesinde)
    tab_r = OxmlElement('w:r')
    tab_el = OxmlElement('w:tab')
    tab_r.append(tab_el)
    hyperlink.addnext(tab_r)

    # Tab'ın ardına sayfa numarası run'ı ekle
    page_r = OxmlElement('w:r')
    pt_el = OxmlElement('w:t')
    pt_el.text = page_text
    page_r.append(pt_el)
    tab_r.addnext(page_r)

    return True


doc = docx.Document(DOCX)

count = 0
for p in doc.paragraphs:
    st = p.style.name.lower()
    # toc 1, toc 2, toc 3 veya T1, T2, T3
    if st.startswith('toc') and st[3:].strip().isdigit():
        if restructure_toc_paragraph(p):
            count += 1
    elif st.startswith('t') and len(st) == 2 and st[1].isdigit():
        if restructure_toc_paragraph(p):
            count += 1

print(f"✓ {count} TOC paragrafı yeniden yapılandırıldı (tab artık hyperlink DIŞINDA)")

doc.save(DOCX)
print("Dosya kaydedildi.")
