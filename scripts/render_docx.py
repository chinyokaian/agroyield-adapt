"""Render a .docx to paginated HTML that mirrors the layout Word will use.

Honours the section's own page size and margins, splits pages on the document's
page breaks, and embeds images, so a visual check reflects the file rather than
a stripped conversion.
"""

from __future__ import annotations

import base64
import html
import sys

from docx import Document
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph


def cm(emu_value) -> float:
    return emu_value / 360000.0


def run_images(p: Paragraph, part) -> str:
    out = []
    for run in p.runs:
        for blip in run._element.findall(".//" + qn("a:blip")):
            rid = blip.get(qn("r:embed"))
            if not rid:
                continue
            blob_part = part.related_parts[rid]
            data = base64.b64encode(blob_part.blob).decode("ascii")
            ext = blob_part.partname.ext.lower()
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            out.append(f'<img src="data:{mime};base64,{data}" style="width:6.5cm;">')
    return "".join(out)


def para_text(p: Paragraph) -> str:
    """Text in document order, including field placeholders and tab characters.

    python-docx's Paragraph.text skips fldSimple content, which would hide the
    table-of-contents placeholders and the SEQ numbers in table captions.
    """
    return "".join(node.text or "" for node in p._p.iter(qn("w:t")))


def para_html(p: Paragraph, part) -> str:
    text = html.escape(para_text(p))
    images = run_images(p, part)
    if not text.strip() and not images:
        return ""
    style = p.style.name if p.style else "Normal"
    run = next((r for r in p.runs if r.text.strip()), None)
    size = run.font.size.pt if (run is not None and run.font.size) else 12
    bold = "font-weight:bold;" if (run is not None and run.bold) else ""
    italic = "font-style:italic;" if (run is not None and run.italic) else ""
    family = run.font.name if (run is not None and run.font.name) else "Times New Roman"
    align = p.alignment
    align_css = "text-align:center;" if align is not None and "CENTER" in str(align) else ""
    fli = p.paragraph_format.first_line_indent
    indent_css = ""
    if fli is not None and fli.cm < 0:
        indent_css = f"text-indent:{fli.cm:.2f}cm; padding-left:{-fli.cm:.2f}cm;"
    spacing = p.paragraph_format.line_spacing or 1.5
    after = p.paragraph_format.space_after
    after_css = f"margin-bottom:{cm(after):.2f}cm;" if after is not None else "margin-bottom:0.2cm;"
    before = p.paragraph_format.space_before
    if before is not None:
        after_css += f"margin-top:{cm(before):.2f}cm;"
    if images and not text.strip():
        return f'<p style="{align_css}margin:0;">{images}</p>'
    if style.startswith("Heading"):
        return (f'<p style="font-family:{family};font-size:14pt;{bold}{align_css}'
                f'margin:0.5cm 0 0.3cm 0;">{text}</p>')
    if style == "List Bullet":
        return (f'<p style="margin:0 0 0.15cm 1.1cm;text-indent:-0.5cm;'
                f'font-size:{size}pt;{bold}{italic}line-height:{spacing};">&bull;&nbsp;{text}</p>')
    return (f'<p style="font-family:{family};font-size:{size}pt;{bold}{italic}{align_css}'
            f'{indent_css}{after_css}line-height:{spacing};">{text}{images}</p>')


def table_html(t: Table, part, content_cm: float) -> str:
    widths = [c.width.cm if c.width is not None else content_cm / len(t.columns)
              for c in t.rows[0].cells]
    total = sum(widths)
    colgroup = "".join(f'<col style="width:{w / total * 100:.2f}%">' for w in widths)
    rows = []
    for r in t.rows:
        cells = []
        for c in r.cells:
            inner = "".join(para_html(p, part) for p in c.paragraphs)
            cells.append(f"<td>{inner}</td>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<table style="width:{content_cm}cm;table-layout:fixed;border-collapse:collapse;'
            f'margin:0.2cm 0 0.4cm 0;font-size:11pt;">'
            f'<colgroup>{colgroup}</colgroup>{"".join(rows)}</table>')


def has_page_break(p: Paragraph) -> bool:
    for br in p._p.findall(".//" + qn("w:br")):
        if br.get(qn("w:type")) == "page":
            return True
    return False


def ends_section(p: Paragraph) -> bool:
    """A section break forces a new page in Word."""
    return p._p.find(qn("w:pPr") + "/" + qn("w:sectPr")) is not None


def render(src: str, dst: str, title: str = "render") -> None:
    doc = Document(src)
    section = doc.sections[0]
    left, right = cm(section.left_margin), cm(section.right_margin)
    top, bottom = cm(section.top_margin), cm(section.bottom_margin)
    width, height = cm(section.page_width), cm(section.page_height)
    content = width - left - right
    part = doc.part  # owns the image relationships

    pages, current = [], []
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, doc)
            if has_page_break(p) or ends_section(p):
                node = para_html(p, part)
                if para_text(p).strip():
                    current.append(node)
                if current:
                    pages.append(current)
                current = []
                continue
            current.append(para_html(p, part))
        elif tag == "tbl":
            current.append(table_html(Table(child, doc), part, content))
    if current:
        pages.append(current)

    css = f"""
    html {{ background:#e8e8e8; }}
    .page {{ background:#fff; width:{width}cm; min-height:{height}cm; box-sizing:border-box;
             padding:{top}cm {right}cm {bottom}cm {left}cm; margin:0 auto 0.6cm auto;
             font-family:"Times New Roman",serif; font-size:12pt; line-height:1.5; color:#000;
             position:relative; box-shadow:0 0 3px rgba(0,0,0,.25); }}
    td {{ border:1px solid #000; padding:0.1cm 0.13cm; vertical-align:top; }}
    td p {{ margin:0 0 0.05cm 0 !important; line-height:1.15 !important; }}
    .pageno {{ position:absolute; bottom:1.6cm; left:0; right:0; text-align:center;
               font-size:11pt; color:#555; }}
    """
    chunks = []
    for i, nodes in enumerate(pages, start=1):
        chunks.append(f'<div class="page">{"".join(nodes)}'
                      f'<div class="pageno">[{i}]</div></div>')
    out = (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title>"
           f"<style>{css}</style></head><body>{''.join(chunks)}</body></html>")
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(out)
    print(f"rendered {len(pages)} pages from {src} -> {dst}")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], title=sys.argv[1].split("/")[-1])
