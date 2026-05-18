"""İlk TOC entry'sinin XML yapısını incele."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import docx
from docx.oxml.ns import qn
from lxml import etree

doc = docx.Document(r'c:\Users\alper\Desktop\CCDDA\docs\ÇocukÇizimlerindenDuyduDurumuAnalizi.docx')

for p in doc.paragraphs:
    if p.text.strip() == 'ÖZET\tvi':
        # XML'ini print et, namespace prefix'leri olmadan
        xml_str = etree.tostring(p._element, pretty_print=True).decode()
        # namespace declarations'ı kısalt
        import re
        xml_str = re.sub(r'xmlns:\w+="[^"]+"', '', xml_str)
        xml_str = re.sub(r'\s+>', '>', xml_str)
        xml_str = re.sub(r'\n\s*\n', '\n', xml_str)
        print(xml_str[:3000])
        break
