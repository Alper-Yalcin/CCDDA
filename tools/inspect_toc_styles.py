"""TOC stillerini ve sayfa düzenini incele."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import docx
from docx.oxml.ns import qn
from lxml import etree
import re

doc = docx.Document(r'c:\Users\alper\Desktop\CCDDA\docs\ÇocukÇizimlerindenDuyduDurumuAnalizi.docx')

# T1, T2, T3 stillerini incele
for st_name in ['toc 1', 'toc 2', 'toc 3', 'T1', 'T2', 'T3']:
    try:
        st = doc.styles[st_name]
        s_elem = st.element
        xml_s = etree.tostring(s_elem, pretty_print=True).decode()
        xml_s = re.sub(r'xmlns:\w+="[^"]+"', '', xml_s)
        print(f'=== Style: {st_name} ===')
        print(xml_s[:1500])
        print()
    except KeyError:
        pass

# Page layout
sec = doc.sections[0]
print('=== Page setup ===')
pw = sec.page_width
lm = sec.left_margin
rm = sec.right_margin
print(f'page_width: {pw} EMU ({pw / 914400:.2f} inch / {pw / 360000:.2f} cm)')
print(f'left_margin: {lm} EMU ({lm / 360000:.2f} cm)')
print(f'right_margin: {rm} EMU ({rm / 360000:.2f} cm)')
usable = pw - lm - rm
print(f'usable width: {usable} EMU ({usable / 360000:.2f} cm)')
print(f'usable in twips: {usable / 635:.0f}')  # 1 twip = 635 EMU
