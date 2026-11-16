"""Render a .docx to HTML that preserves the layout Word will use.

Mammoth drops alignment, indentation and column widths, so a page rendered from
it cannot show whether a table column is wide enough or a title is centred.
This renderer reads those properties from the document itself, so the visual
check reflects the file rather than a stripped-down conversion.
"""

from __future__ import annotations

import html
import sys

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

CONTENT_CM = 15.46  # A4 minus 3.0 cm left and 2.54 cm right margins


def para_html(p: Paragraph) -> str:
    text = html.escape(p.text)
    if not text.strip():
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
    if style.startswith("Heading"):
        level = "h1" if style == "Heading 1" else "h2"
        return (f'<{level} style="font-family:{family};font-size:14pt;{bold}'
                f'{align_css}margin:18pt 0 8pt 0;">{text}</{level}>')
    if style == "List Bullet":
        return (f'<p style="margin:0 0 4pt 1.1cm;text-indent:-0.5cm;'
                f'font-size:{size}pt;{bold}{italic}line-height:{spacing};">&bull;&nbsp;&nbsp;{text}</p>')
    return (f'<p style="font-family:{family};font-size:{size}pt;{bold}{italic}{align_css}'
            f'{indent_css}margin:0 0 7pt 0;line-height:{spacing};">{text}</p>')


def table_html(t: Table) -> str:
    widths = [c.width.cm if c.width is not None else CONTENT_CM / len(t.columns)
              for c in t.rows[0].cells]
    total = sum(widths)
    colgroup = "".join(f'<col style="width:{w / total * 100:.2f}%">' for w in widths)
    rows = []
    for r in t.rows:
        cells = []
        for c in r.cells:
            inner = "".join(para_html(p) for p in c.paragraphs)
            cells.append(f'<td style="valign:top;">{inner}</td>')
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return (f'<table style="width:{CONTENT_CM}cm;table-layout:fixed;border-collapse:collapse;'
            f'margin:8pt 0 14pt 0;font-size:11pt;">'
            f'<colgroup>{colgroup}</colgroup>{"".join(rows)}</table>')


def render(src: str, dst: str, title: str = "render") -> None:
    doc = Document(src)
    body = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            body.append(para_html(Paragraph(child, doc)))
        elif tag == "tbl":
            body.append(table_html(Table(child, doc)))
    css = f"""
    @page {{ size: A4; margin: 2.54cm 2.54cm 2.54cm 3.0cm; }}
    html {{ background:#f0f0f0; }}
    .page {{ background:#fff; width:21cm; min-height:29.7cm; box-sizing:border-box;
             padding:2.54cm 2.54cm 2.54cm 3.0cm; margin:0 auto; }}
    body {{ font-family:"Times New Roman",serif; font-size:12pt; line-height:1.5; color:#000; }}
    td {{ border:1px solid #000; padding:4pt 5pt; vertical-align:top; }}
    td p {{ margin:0 0 2pt 0 !important; line-height:1.15 !important; }}
    """
    doc_html = (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title>"
                f"<style>{css}</style></head><body><div class='page'>"
                f"{''.join(body)}</div></body></html>")
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write(doc_html)
    print(f"rendered {src} -> {dst}")


if __name__ == "__main__":
    render(sys.argv[1], sys.argv[2], title=sys.argv[1].split("/")[-1])
