#!/usr/bin/env python3
"""Build The Long Siege manuscript into a formatted print-ready PDF (ReportLab)."""
from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.flowables import Flowable
from reportlab.platypus.tableofcontents import TableOfContents

PROJECT = Path(__file__).resolve().parents[1]
CHAPTERS = sorted((PROJECT / "06_chapters").glob("chapter_*.md"))
OUT = PROJECT / "The_Long_Siege.pdf"
FONT_DIR = PROJECT / "build" / "fonts"

INK = HexColor("#1c1a17")
SOFT_INK = HexColor("#55504a")
RULE = HexColor("#8a8177")

# ---------------------------------------------------------------- fonts
pdfmetrics.registerFont(TTFont("Serif", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Italic", str(FONT_DIR / "DejaVuSerif-Oblique.ttf")))
pdfmetrics.registerFont(
    TTFont("Serif-BoldItalic", str(FONT_DIR / "DejaVuSerif-BoldOblique.ttf"))
)
pdfmetrics.registerFontFamily(
    "Serif",
    normal="Serif",
    bold="Serif-Bold",
    italic="Serif-Italic",
    boldItalic="Serif-BoldItalic",
)

# ---------------------------------------------------------------- styles
styles = getSampleStyleSheet()

body = ParagraphStyle(
    "Body",
    parent=styles["Normal"],
    fontName="Serif",
    fontSize=10.5,
    leading=15.5,
    alignment=TA_JUSTIFY,
    textColor=INK,
    spaceAfter=7,
    firstLineIndent=16,
    allowWidows=0,
    allowOrphans=0,
)
body_noindent = ParagraphStyle("BodyNoIndent", parent=body, firstLineIndent=0)
scene = ParagraphStyle(
    "Scene", parent=body, alignment=TA_CENTER, firstLineIndent=0,
    spaceBefore=10, spaceAfter=10, textColor=SOFT_INK,
)
chapter_num = ParagraphStyle(
    "ChapterNum",
    parent=styles["Normal"],
    fontName="Serif",
    fontSize=11,
    leading=14,
    alignment=TA_CENTER,
    textColor=SOFT_INK,
    spaceAfter=6,
    tracking=2.5,
)
chapter_title = ParagraphStyle(
    "ChapterTitle",
    parent=styles["Normal"],
    fontName="Serif-Bold",
    fontSize=19,
    leading=24,
    alignment=TA_CENTER,
    textColor=INK,
    spaceAfter=6,
)
title_rule = ParagraphStyle(
    "TitleRule", parent=styles["Normal"], alignment=TA_CENTER, textColor=RULE
)
toc_title = ParagraphStyle(
    "TOCTitle", parent=chapter_title, fontSize=20, spaceAfter=26
)
toc0 = ParagraphStyle(
    "TOC0",
    parent=styles["Normal"],
    fontName="Serif",
    fontSize=11,
    leading=20,
    textColor=INK,
)
cover_title = ParagraphStyle(
    "CoverTitle",
    parent=styles["Normal"],
    fontName="Serif-Bold",
    fontSize=34,
    leading=42,
    alignment=TA_CENTER,
    textColor=INK,
)
cover_sub = ParagraphStyle(
    "CoverSub",
    parent=styles["Normal"],
    fontName="Serif-Italic",
    fontSize=15,
    leading=22,
    alignment=TA_CENTER,
    textColor=SOFT_INK,
)
copyright_style = ParagraphStyle(
    "Copyright",
    parent=styles["Normal"],
    fontName="Serif",
    fontSize=9,
    leading=13.5,
    alignment=TA_LEFT,
    textColor=SOFT_INK,
)


# ---------------------------------------------------------------- helpers
def md_inline(text: str) -> str:
    """Escape XML, then convert _italic_ and **bold** into ReportLab markup."""
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<i>\1</i>", text)
    return text


def load_chapter(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    heading = lines[0].lstrip("# ").strip()
    m = re.match(r"Chapter\s+(.+?)\s+[—-]\s+(.+)", heading)
    if m:
        num_word, name = m.group(1), m.group(2)
        num_display = f"CHAPTER {num_word.upper()}"
    else:
        num_word, name, num_display = "", heading, heading
    blocks, para = [], []
    for line in lines[1:]:
        line = line.strip()
        if not line:
            if para:
                blocks.append(" ".join(para))
                para = []
        elif line == "* * *":
            if para:
                blocks.append(" ".join(para))
                para = []
            blocks.append("* * *")
        else:
            para.append(line)
    if para:
        blocks.append(" ".join(para))
    return num_display, name, blocks


class Dropcap(Flowable):
    """Three-line drop cap built from a borderless two-cell table."""

    CAP_W = 0.42 * inch
    GAP = 0.08 * inch

    def __init__(self, text: str, avail_width: float):
        super().__init__()
        self.text = text
        self.avail_width = avail_width
        self._table = None
        self._build()

    def _build(self):
        words = self.text.split()
        cap = words[0][0]
        rest = " ".join(words[1:])
        reduced = self.avail_width - self.CAP_W - self.GAP
        cap_style = ParagraphStyle(
            "Cap",
            fontName="Serif-Bold",
            fontSize=38,
            leading=40,
            alignment=TA_LEFT,
            textColor=INK,
        )
        # Find the word count that fills three lines in the reduced width.
        head_words, tail_words = len(words) - 1, 0
        for take in range(len(words) - 1, 0, -1):
            p = Paragraph(md_inline(" ".join(words[1:1 + take])), body_noindent)
            w, h = p.wrap(reduced, 10_000)
            line_count = max(1, round(h / body.leading))
            if line_count <= 3:
                head_words = take
                break
        head = Paragraph(md_inline(" ".join(words[1:1 + head_words])), body_noindent)
        tail = " ".join(words[1 + head_words:])
        cap_p = Paragraph(cap, cap_style)
        t = Table(
            [[cap_p, head]],
            colWidths=[self.CAP_W, reduced],
            hAlign="LEFT",
        )
        t.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ("LEFTPADDING", (1, 0), (1, 0), self.GAP),
                ]
            )
        )
        self._table = t
        self._tail = tail

    def wrap(self, availWidth, availHeight):
        w, h = self._table.wrap(availWidth, availHeight)
        return availWidth, h

    def draw(self):
        self._table.drawOn(self.canv, 0, 0)

    def tail(self) -> str:
        return self._tail


class BookDoc(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_chapter = ""
        self.body_start_physical = None
        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="book",
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
        )
        self.addPageTemplates(
            [
                PageTemplate(id="front", frames=[frame], onPage=self._front_page),
                PageTemplate(id="body", frames=[frame], onPage=self._body_page),
            ]
        )

    def handle_documentBegin(self):
        super().handle_documentBegin()
        self.current_chapter = ""
        self.body_start_physical = None

    def handle_pageBegin(self):
        super().handle_pageBegin()
        if (
            self.body_start_physical is None
            and self.pageTemplate.id == "body"
        ):
            self.body_start_physical = self.page

    def _logical_page(self):
        if self.body_start_physical is None:
            return None
        return self.page - self.body_start_physical + 1

    def _front_page(self, canv, doc):
        return  # front matter carries no running heads or folios

    def _body_page(self, canv, doc):
        logical = self._logical_page()
        if logical is None:
            return
        canv.saveState()
        canv.setFont("Serif-Italic", 8.5)
        canv.setFillColor(SOFT_INK)
        y = doc.pagesize[1] - 0.55 * inch
        if logical % 2 == 0:  # verso: book title
            canv.drawString(doc.leftMargin, y, "The Long Siege")
        else:  # recto: chapter title
            canv.drawRightString(
                doc.pagesize[0] - doc.rightMargin, y, self.current_chapter
            )
        canv.setStrokeColor(RULE)
        canv.setLineWidth(0.4)
        canv.line(
            doc.leftMargin,
            y - 4,
            doc.pagesize[0] - doc.rightMargin,
            y - 4,
        )
        canv.setFont("Serif", 9)
        canv.drawCentredString(
            doc.pagesize[0] / 2, 0.45 * inch, str(logical)
        )
        canv.restoreState()

    def afterFlowable(self, flowable):
        if flowable.__class__.__name__ == "Paragraph":
            style = flowable.style.name
            if style == "ChapterTitle":
                text = flowable.getPlainText()
                self.current_chapter = text
                logical = self._logical_page() or self.page
                self.notify("TOCEntry", (0, text, logical))


# ---------------------------------------------------------------- build story
def build():
    doc = BookDoc(
        str(OUT),
        pagesize=(5.5 * inch, 8.5 * inch),
        leftMargin=0.85 * inch,
        rightMargin=0.85 * inch,
        topMargin=0.95 * inch,
        bottomMargin=0.85 * inch,
        title="The Long Siege",
        author="",
    )
    story = []

    # ---- half title
    story.append(Spacer(1, 2.6 * inch))
    story.append(Paragraph("THE LONG SIEGE", cover_title))
    story.append(PageBreak())

    # ---- title page
    story.append(Spacer(1, 1.7 * inch))
    story.append(Paragraph("THE LONG SIEGE", cover_title))
    story.append(Spacer(1, 0.25 * inch))
    story.append(Paragraph("A Novel", cover_sub))
    story.append(PageBreak())

    # ---- copyright / rating
    story.append(Spacer(1, 2.4 * inch))
    notice = (
        "<b>THE LONG SIEGE</b><br/><br/>"
        "This is a work of historical fiction. Names, characters, places, and "
        "incidents are the products of the author's imagination or are used "
        "fictitiously. Any resemblance to actual persons, living or dead, or "
        "events is entirely coincidental.<br/><br/>"
        "<b>Age rating: Mature / 18+.</b> This novel contains graphic depictions "
        "of warfare and its aftermath, explicit sexual content, violence, and "
        "themes intended for adult readers.<br/><br/>"
        "Set in a fictional dominion amid the real courts and conflicts of "
        "late fifteenth-century Europe.<br/><br/>"
        "All rights reserved. No part of this publication may be reproduced, "
        "stored in a retrieval system, or transmitted in any form or by any "
        "means without the prior written permission of the copyright holder."
    )
    story.append(Paragraph(notice, copyright_style))
    story.append(PageBreak())

    # ---- contents
    story.append(Paragraph("CONTENTS", toc_title))
    toc = TableOfContents()
    toc.levelStyles = [toc0]
    story.append(toc)
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # ---- chapters
    for idx, path in enumerate(CHAPTERS):
        num_display, name, blocks = load_chapter(path)
        story.append(Paragraph(num_display, chapter_num))
        story.append(Paragraph(html.escape(name), chapter_title))
        story.append(Spacer(1, 0.28 * inch))
        first_text = True
        for block in blocks:
            if block == "* * *":
                story.append(Paragraph("* * *", scene))
                continue
            if first_text:
                cap = Dropcap(block, doc.width)
                story.append(cap)
                if cap.tail():
                    story.append(Paragraph(md_inline(cap.tail()), body))
                first_text = False
            else:
                story.append(Paragraph(md_inline(block), body))
        if idx != len(CHAPTERS) - 1:
            story.append(PageBreak())

    doc.multiBuild(story)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
