"""Render the shared report content; no raw data or model loading is involved."""

import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

try:
    from .build_handover import refresh_manifest
except ImportError:
    from build_handover import refresh_manifest

ROOT = Path(__file__).resolve().parents[1]


def render(root=ROOT):
    folder = root / "report"
    content = json.loads((folder / "report_content.json").read_text(encoding="utf-8"))
    output = folder / "ml_contribution.pdf"
    doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=48, leftMargin=48, topMargin=44, bottomMargin=42,
                           title="Blue Mountains Bushfire Prediction ML Contribution", author="Kian Luo", invariant=1)
    body = ParagraphStyle("MLBody", fontName="Helvetica", fontSize=10.2, leading=13.4, spaceAfter=8, textColor=colors.black)
    heading = ParagraphStyle("MLHeading", parent=body, fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=5, spaceAfter=6, keepWithNext=True)
    title = ParagraphStyle("MLTitle", parent=heading, fontSize=15, leading=19, spaceAfter=5)
    page_title = ParagraphStyle("MLPageTitle", parent=heading, fontSize=13, leading=17, spaceAfter=10)
    cell = ParagraphStyle("MLCell", parent=body, fontSize=9, leading=11.5, spaceAfter=0)
    caption = ParagraphStyle("MLCaption", parent=body, fontSize=8.3, leading=10.8, spaceAfter=8)
    reference_style = ParagraphStyle("MLReference", parent=body, fontSize=7.4, leading=9.4, spaceAfter=3)
    story = []
    for index, page in enumerate(content["pages"]):
        if index:
            story.append(PageBreak())
        else:
            story.extend([Paragraph(escape(content["project"]), title), Paragraph(escape(content["title"]), heading), Spacer(1, 5)])
        story.append(Paragraph(escape(page["title"]), page_title))
        for block in page["blocks"]:
            if block["type"] in {"paragraph", "heading"}:
                story.append(Paragraph(escape(block["text"]), heading if block["type"] == "heading" else body))
            elif block["type"] == "table":
                rows = [[Paragraph(escape(str(value)), cell) for value in block["headers"]]]
                rows += [[Paragraph(escape(str(value)), cell) for value in row] for row in block["rows"]]
                table = Table(rows, colWidths=[doc.width*value for value in block["widths"]], repeatRows=1, hAlign="LEFT")
                table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EDEFF2")),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.black),
                    ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#9CA3AF")),
                    ("LINEBELOW", (0, 1), (-1, -1), 0.25, colors.HexColor("#D9DDE3")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ]))
                story.extend([table, Spacer(1, 8)])
            else:
                image = Image(str(folder / block["path"]))
                ratio = min(doc.width/image.imageWidth, block["height"]/image.imageHeight)
                image.drawWidth, image.drawHeight = image.imageWidth*ratio, image.imageHeight*ratio
                image.hAlign = "CENTER"
                story.extend([image, Paragraph(escape(block["caption"]), caption)])
        if index == len(content["pages"])-1:
            story.append(Paragraph("References", heading))
            for number, item in enumerate(content["references"], start=1):
                text = f"[{number}] {item['author'].replace('{', '').replace('}', '')}. {item['title']}. {item['year']}."
                story.append(Paragraph(escape(text)+f' <link href="{escape(item["url"])}" color="black">Source</link>.', reference_style))

    def footer(canvas, document):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#475569"))
        canvas.drawString(48, 25, "ENGG2112  |  ML contribution  |  Frozen results unchanged")
        canvas.drawRightString(A4[0]-48, 25, str(document.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    refresh_manifest(root)
    print(json.dumps({"output": output.relative_to(root).as_posix(), "raw_data_read": False, "model_fitting": False}))


if __name__ == "__main__":
    render()
