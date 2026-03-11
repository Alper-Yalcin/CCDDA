#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import re
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WP_NS = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC_NS = "http://schemas.openxmlformats.org/drawingml/2006/picture"


ET.register_namespace("w", W_NS)
ET.register_namespace("r", R_NS)
ET.register_namespace("wp", WP_NS)
ET.register_namespace("a", A_NS)
ET.register_namespace("pic", PIC_NS)


def qn(tag: str) -> str:
    prefix, local = tag.split(":")
    ns_map = {
        "w": W_NS,
        "r": R_NS,
        "wp": WP_NS,
        "a": A_NS,
        "pic": PIC_NS,
    }
    return f"{{{ns_map[prefix]}}}{local}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a DOCX project report from Markdown using a reference DOCX template."
    )
    parser.add_argument("--markdown", required=True, help="Path to input Markdown file.")
    parser.add_argument("--reference-docx", required=True, help="Path to reference DOCX template.")
    parser.add_argument("--output", required=True, help="Path to output DOCX file.")
    return parser.parse_args()


def clean_text(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
    return text.strip()


def clean_heading_text(text: str) -> str:
    # Word heading styles in the reference template already apply multilevel numbering.
    # Remove manual numbering from Markdown headings to avoid duplicates like "5.2 3.2".
    return re.sub(r"^\d+(?:\.\d+)*\.?\s+", "", text).strip()


def split_table_row(line: str) -> list[str]:
    row = line.strip().strip("|")
    cells = [clean_text(cell.strip()) for cell in row.split("|")]
    return cells


def parse_markdown(md_path: Path) -> list[dict]:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    blocks: list[dict] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        heading_match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading_match:
            level = len(heading_match.group(1))
            text = clean_text(heading_match.group(2))
            blocks.append({"type": "heading", "level": level, "text": text})
            i += 1
            continue

        image_match = re.match(r"^!\[(.*?)\]\((.*?)\)$", stripped)
        if image_match:
            alt = clean_text(image_match.group(1))
            rel_path = image_match.group(2).strip()
            blocks.append({"type": "image", "alt": alt, "path": rel_path})
            i += 1
            continue

        if stripped.startswith("- "):
            items: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                items.append(clean_text(lines[i].strip()[2:]))
                i += 1
            blocks.append({"type": "list", "items": items})
            continue

        if stripped.startswith("|"):
            table_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1

            rows = [split_table_row(row) for row in table_lines]
            if len(rows) >= 2 and all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in rows[1]):
                header = rows[0]
                data = rows[2:]
            else:
                header = rows[0]
                data = rows[1:]
            blocks.append({"type": "table", "header": header, "rows": data})
            continue

        if re.fullmatch(r"-{3,}", stripped):
            i += 1
            continue

        para_lines = [stripped]
        i += 1
        while i < len(lines):
            nxt = lines[i].strip()
            if not nxt:
                break
            if re.match(r"^(#{1,6})\s+", nxt):
                break
            if nxt.startswith("- "):
                break
            if nxt.startswith("|"):
                break
            if re.match(r"^!\[(.*?)\]\((.*?)\)$", nxt):
                break
            if re.fullmatch(r"-{3,}", nxt):
                break
            para_lines.append(nxt)
            i += 1
        blocks.append({"type": "paragraph", "text": clean_text(" ".join(para_lines))})
    return blocks


def make_paragraph(text: str, style: str | None = None, center: bool = False) -> ET.Element:
    p = ET.Element(qn("w:p"))
    p_pr = ET.SubElement(p, qn("w:pPr"))
    if style:
        p_style = ET.SubElement(p_pr, qn("w:pStyle"))
        p_style.set(qn("w:val"), style)
    if center:
        jc = ET.SubElement(p_pr, qn("w:jc"))
        jc.set(qn("w:val"), "center")

    run = ET.SubElement(p, qn("w:r"))
    text_el = ET.SubElement(run, qn("w:t"))
    if text.startswith(" ") or text.endswith(" "):
        text_el.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text_el.text = text
    return p


def make_table(table_block: dict) -> ET.Element:
    header = table_block["header"]
    rows = table_block["rows"]
    col_count = max(len(header), *(len(row) for row in rows)) if rows else len(header)

    tbl = ET.Element(qn("w:tbl"))
    tbl_pr = ET.SubElement(tbl, qn("w:tblPr"))
    tbl_style = ET.SubElement(tbl_pr, qn("w:tblStyle"))
    tbl_style.set(qn("w:val"), "TabloKlavuzu")
    tbl_w = ET.SubElement(tbl_pr, qn("w:tblW"))
    tbl_w.set(qn("w:w"), "0")
    tbl_w.set(qn("w:type"), "auto")
    tbl_look = ET.SubElement(tbl_pr, qn("w:tblLook"))
    tbl_look.set(qn("w:val"), "04A0")
    tbl_look.set(qn("w:firstRow"), "1")
    tbl_look.set(qn("w:lastRow"), "0")
    tbl_look.set(qn("w:firstColumn"), "1")
    tbl_look.set(qn("w:lastColumn"), "0")
    tbl_look.set(qn("w:noHBand"), "0")
    tbl_look.set(qn("w:noVBand"), "1")

    tbl_grid = ET.SubElement(tbl, qn("w:tblGrid"))
    for _ in range(col_count):
        grid_col = ET.SubElement(tbl_grid, qn("w:gridCol"))
        grid_col.set(qn("w:w"), "2400")

    def add_row(cells: list[str], is_header: bool = False) -> None:
        tr = ET.SubElement(tbl, qn("w:tr"))
        for idx in range(col_count):
            tc = ET.SubElement(tr, qn("w:tc"))
            tc_pr = ET.SubElement(tc, qn("w:tcPr"))
            tc_w = ET.SubElement(tc_pr, qn("w:tcW"))
            tc_w.set(qn("w:w"), "2400")
            tc_w.set(qn("w:type"), "dxa")
            if is_header:
                shd = ET.SubElement(tc_pr, qn("w:shd"))
                shd.set(qn("w:val"), "clear")
                shd.set(qn("w:color"), "auto")
                shd.set(qn("w:fill"), "D9D9D9")

            cell_text = cells[idx] if idx < len(cells) else ""
            p = make_paragraph(cell_text, style="Tabloerii")
            tc.append(p)

    add_row(header, is_header=True)
    for row in rows:
        add_row(row, is_header=False)
    return tbl


def get_png_size(path: Path) -> tuple[int, int]:
    with path.open("rb") as fh:
        header = fh.read(24)
    if header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        raise ValueError(f"Unsupported PNG file: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def compute_image_extents(path: Path, max_width_in: float = 6.3, max_height_in: float = 8.0) -> tuple[int, int]:
    width_px, height_px = get_png_size(path)
    width_in = width_px / 96.0
    height_in = height_px / 96.0
    scale = min(max_width_in / width_in, max_height_in / height_in, 1.0)
    width_emu = int(width_in * scale * 914400)
    height_emu = int(height_in * scale * 914400)
    return width_emu, height_emu


def make_image_paragraph(rel_id: str, image_name: str, doc_pr_id: int, cx: int, cy: int) -> ET.Element:
    p = ET.Element(qn("w:p"))
    p_pr = ET.SubElement(p, qn("w:pPr"))
    jc = ET.SubElement(p_pr, qn("w:jc"))
    jc.set(qn("w:val"), "center")

    run = ET.SubElement(p, qn("w:r"))
    drawing = ET.SubElement(run, qn("w:drawing"))
    inline = ET.SubElement(drawing, qn("wp:inline"))
    inline.set("distT", "0")
    inline.set("distB", "0")
    inline.set("distL", "0")
    inline.set("distR", "0")

    extent = ET.SubElement(inline, qn("wp:extent"))
    extent.set("cx", str(cx))
    extent.set("cy", str(cy))

    doc_pr = ET.SubElement(inline, qn("wp:docPr"))
    doc_pr.set("id", str(doc_pr_id))
    doc_pr.set("name", image_name)

    c_nv = ET.SubElement(inline, qn("wp:cNvGraphicFramePr"))
    frame_locks = ET.SubElement(c_nv, qn("a:graphicFrameLocks"))
    frame_locks.set("noChangeAspect", "1")

    graphic = ET.SubElement(inline, qn("a:graphic"))
    graphic_data = ET.SubElement(graphic, qn("a:graphicData"))
    graphic_data.set("uri", PIC_NS)

    pic = ET.SubElement(graphic_data, qn("pic:pic"))
    nv_pic_pr = ET.SubElement(pic, qn("pic:nvPicPr"))
    c_nv_pr = ET.SubElement(nv_pic_pr, qn("pic:cNvPr"))
    c_nv_pr.set("id", "0")
    c_nv_pr.set("name", image_name)
    ET.SubElement(nv_pic_pr, qn("pic:cNvPicPr"))

    blip_fill = ET.SubElement(pic, qn("pic:blipFill"))
    blip = ET.SubElement(blip_fill, qn("a:blip"))
    blip.set(qn("r:embed"), rel_id)
    stretch = ET.SubElement(blip_fill, qn("a:stretch"))
    ET.SubElement(stretch, qn("a:fillRect"))

    sp_pr = ET.SubElement(pic, qn("pic:spPr"))
    xfrm = ET.SubElement(sp_pr, qn("a:xfrm"))
    off = ET.SubElement(xfrm, qn("a:off"))
    off.set("x", "0")
    off.set("y", "0")
    ext = ET.SubElement(xfrm, qn("a:ext"))
    ext.set("cx", str(cx))
    ext.set("cy", str(cy))
    prst_geom = ET.SubElement(sp_pr, qn("a:prstGeom"))
    prst_geom.set("prst", "rect")
    ET.SubElement(prst_geom, qn("a:avLst"))
    return p


def next_relationship_id(rels_root: ET.Element) -> int:
    max_id = 0
    for rel in rels_root.findall(f"{{{REL_NS}}}Relationship"):
        rel_id = rel.attrib.get("Id", "")
        match = re.fullmatch(r"rId(\d+)", rel_id)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return max_id + 1


def style_for_heading(level: int) -> str:
    if level == 1:
        return "Balk"
    if level == 2:
        return "Balk1"
    if level == 3:
        return "Balk2"
    if level == 4:
        return "Balk3"
    return "Balk4"


def build_docx(markdown_path: Path, reference_docx: Path, output_docx: Path) -> None:
    blocks = parse_markdown(markdown_path)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        with zipfile.ZipFile(reference_docx, "r") as zf:
            zf.extractall(temp_root)

        document_xml = temp_root / "word" / "document.xml"
        rels_xml = temp_root / "word" / "_rels" / "document.xml.rels"
        media_dir = temp_root / "word" / "media"
        media_dir.mkdir(parents=True, exist_ok=True)

        doc_tree = ET.parse(document_xml)
        doc_root = doc_tree.getroot()
        body = doc_root.find(qn("w:body"))
        if body is None:
            raise RuntimeError("Reference DOCX body not found.")

        sect_pr = body.find(qn("w:sectPr"))
        preserved_sect = ET.fromstring(ET.tostring(sect_pr)) if sect_pr is not None else None
        body.clear()

        rels_tree = ET.parse(rels_xml)
        rels_root = rels_tree.getroot()
        rel_counter = next_relationship_id(rels_root)
        doc_pr_id = 100

        for block in blocks:
            block_type = block["type"]
            if block_type == "heading":
                body.append(
                    make_paragraph(
                        clean_heading_text(block["text"]),
                        style=style_for_heading(block["level"]),
                    )
                )
            elif block_type == "paragraph":
                if block["text"]:
                    body.append(make_paragraph(block["text"], style="Metin"))
            elif block_type == "list":
                for item in block["items"]:
                    body.append(make_paragraph(f"• {item}", style="ListeParagraf"))
            elif block_type == "table":
                body.append(make_table(block))
            elif block_type == "image":
                image_source = (markdown_path.parent / block["path"]).resolve()
                if not image_source.exists():
                    body.append(
                        make_paragraph(
                            f"[Görsel bulunamadı: {block['path']}]",
                            style="Metin",
                        )
                    )
                    continue

                target_name = f"report_figure_{doc_pr_id}.png"
                shutil.copyfile(image_source, media_dir / target_name)

                rel_id = f"rId{rel_counter}"
                rel_counter += 1
                relationship = ET.SubElement(rels_root, f"{{{REL_NS}}}Relationship")
                relationship.set("Id", rel_id)
                relationship.set(
                    "Type",
                    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image",
                )
                relationship.set("Target", f"media/{target_name}")

                cx, cy = compute_image_extents(image_source)
                body.append(make_image_paragraph(rel_id, target_name, doc_pr_id, cx, cy))
                doc_pr_id += 1

        if preserved_sect is not None:
            body.append(preserved_sect)

        doc_tree.write(document_xml, encoding="utf-8", xml_declaration=True)
        rels_tree.write(rels_xml, encoding="utf-8", xml_declaration=True)

        output_docx.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_docx, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _, files in os.walk(temp_root):
                for file_name in files:
                    full_path = Path(root) / file_name
                    arc_name = full_path.relative_to(temp_root).as_posix()
                    zf.write(full_path, arc_name)


def main() -> None:
    args = parse_args()
    build_docx(
        markdown_path=Path(args.markdown),
        reference_docx=Path(args.reference_docx),
        output_docx=Path(args.output),
    )
    print(f"DOCX olusturuldu: {args.output}")


if __name__ == "__main__":
    main()
