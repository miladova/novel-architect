#!/usr/bin/env python3
"""Illuminated-manuscript PDF builder for *The Long Siege*.

All illumination (vine borders, gilded initials, fleurons, rules) is drawn
as vector art on a parchment ground; the only raster asset is the
frontispiece. Run from the repository root:

    .venv/bin/python novels/the-long-siege/build/build_pdf.py
"""
import html
import math
import re
from pathlib import Path

from reportlab.lib.colors import Color
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

# ---------------------------------------------------------------- paths
PROJECT = Path(__file__).resolve().parents[1]
CHAPTERS = PROJECT / "06_chapters"
FONT_DIR = PROJECT / "build" / "fonts"
ASSETS = PROJECT / "build" / "assets"
OUT_PDF = PROJECT / "The_Long_Siege.pdf"

PAGE_W, PAGE_H = 5.5 * inch, 8.5 * inch
MARGIN_L = MARGIN_R = 0.85 * inch
MARGIN_T = 0.95 * inch
MARGIN_B = 0.85 * inch

# ---------------------------------------------------------------- palette
PARCHMENT = Color(0.985, 0.966, 0.928)
INK = Color(0.145, 0.105, 0.078)
SOFT_INK = Color(0.30, 0.23, 0.18)
GOLD = Color(0.715, 0.545, 0.165)
LIGHT_GOLD = Color(0.845, 0.705, 0.385)
CRIMSON = Color(0.495, 0.105, 0.130)
BLUE = Color(0.135, 0.205, 0.420)
GREEN = Color(0.235, 0.335, 0.170)
DEEP_GREEN = Color(0.165, 0.255, 0.125)
RULE_GOLD = Color(0.76, 0.63, 0.36)

# ---------------------------------------------------------------- fonts
pdfmetrics.registerFont(
    TTFont("Serif", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")
)
pdfmetrics.registerFont(
    TTFont("Serif-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf")
)
pdfmetrics.registerFont(
    TTFont("Serif-Italic", str(FONT_DIR / "DejaVuSerif-Oblique.ttf"))
)
pdfmetrics.registerFont(
    TTFont(
        "Serif-BoldItalic",
        str(FONT_DIR / "DejaVuSerif-BoldOblique.ttf"),
    )
)
pdfmetrics.registerFontFamily(
    "Serif",
    normal="Serif",
    bold="Serif-Bold",
    italic="Serif-Italic",
    boldItalic="Serif-BoldItalic",
)

# ---------------------------------------------------------------- styles
body = ParagraphStyle(
    "Body",
    fontName="Serif",
    fontSize=10.5,
    leading=15.5,
    alignment=TA_JUSTIFY,
    firstLineIndent=14,
    textColor=INK,
    spaceAfter=0,
)
body_noindent = ParagraphStyle(
    "BodyNoIndent", parent=body, firstLineIndent=0
)
front_text = ParagraphStyle(
    "FrontText",
    fontName="Serif",
    fontSize=10,
    leading=15,
    alignment=TA_CENTER,
    textColor=SOFT_INK,
)
toc0 = ParagraphStyle(
    "TOC0",
    fontName="Serif",
    fontSize=10.5,
    leading=20,
    leftIndent=6,
    firstLineIndent=-6,
    textColor=INK,
)


# ================================================================ ornament art
def draw_leaf(c, x, y, angle, size, color=GREEN):
    """Pointed leaf with a gold vein; origin at the stem end."""
    c.saveState()
    c.translate(x, y)
    c.rotate(angle)
    p = c.beginPath()
    p.moveTo(0, 0)
    p.curveTo(size * 0.45, size * 0.30, size * 0.88, size * 0.26, size, 0)
    p.curveTo(size * 0.88, -size * 0.26, size * 0.45, -size * 0.30, 0, 0)
    c.setFillColor(color)
    c.setStrokeColor(DEEP_GREEN)
    c.setLineWidth(0.25)
    c.drawPath(p, stroke=1, fill=1)
    c.setStrokeColor(LIGHT_GOLD)
    c.setLineWidth(0.3)
    c.line(size * 0.08, 0, size * 0.9, 0)
    c.restoreState()


def draw_flower(c, x, y, r, petal=CRIMSON, center=GOLD):
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        c.setFillColor(petal)
        c.circle(
            x + math.cos(a) * r * 0.66,
            y + math.sin(a) * r * 0.66,
            r * 0.44,
            stroke=0,
            fill=1,
        )
    c.setFillColor(center)
    c.circle(x, y, r * 0.34, stroke=0, fill=1)


def draw_berry(c, x, y, r, color=BLUE):
    c.setFillColor(color)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.4)
    c.circle(x, y, r, stroke=1, fill=1)
    c.setFillColor(LIGHT_GOLD)
    c.circle(x - r * 0.3, y + r * 0.3, r * 0.22, stroke=0, fill=1)


def tracked_width(c, text, font, size, char_space):
    return c.stringWidth(text, font, size) + char_space * max(
        0, len(text) - 1
    )


def draw_tracked(c, text, x, y, font, size, color, char_space):
    """Draw char-spaced text via a PDF text object (RL5 API)."""
    t = c.beginText(x, y)
    t.setFont(font, size)
    t.setFillColor(color)
    t.setCharSpace(char_space)
    t.textOut(text)
    c.drawText(t)


def draw_diamond(c, x, y, r, color=GOLD):
    c.saveState()
    c.translate(x, y)
    c.rotate(45)
    c.setFillColor(color)
    c.rect(-r, -r, 2 * r, 2 * r, stroke=0, fill=1)
    c.restoreState()


def draw_corner_vine(c, px, py, sx, sy, scale=1.0):
    """Illuminated corner growing inward from (px, py). sx/sy are signs."""
    c.saveState()
    c.translate(px, py)
    c.scale(sx * scale, sy * scale)
    # main stem
    c.setStrokeColor(DEEP_GREEN)
    c.setLineWidth(0.9)
    p = c.beginPath()
    p.moveTo(0, 0)
    p.curveTo(28, 6, 46, 22, 62, 44)
    p.curveTo(74, 60, 86, 66, 104, 68)
    c.drawPath(p, stroke=1, fill=0)
    # side stem climbing the vertical edge
    p2 = c.beginPath()
    p2.moveTo(0, 0)
    p2.curveTo(6, 26, 20, 44, 40, 58)
    p2.curveTo(54, 68, 64, 74, 70, 92)
    c.drawPath(p2, stroke=1, fill=0)
    # leaves along horizontal stem
    draw_leaf(c, 22, 8, 28, 11)
    draw_leaf(c, 44, 26, -32, 10, DEEP_GREEN)
    draw_leaf(c, 66, 48, 24, 11)
    draw_leaf(c, 88, 64, -18, 9)
    # leaves along vertical stem
    draw_leaf(c, 8, 24, 62, 10)
    draw_leaf(c, 26, 46, 118, 10, DEEP_GREEN)
    draw_leaf(c, 48, 66, 70, 9)
    # flowers and berries
    draw_flower(c, 100, 70, 6.5, petal=CRIMSON)
    draw_flower(c, 66, 92, 5.5, petal=BLUE)
    draw_berry(c, 34, 16, 3.2)
    draw_berry(c, 58, 58, 3.0, CRIMSON)
    draw_berry(c, 16, 52, 3.0)
    # gold ring medallion at the corner
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.1)
    c.circle(2, 2, 10, stroke=1, fill=0)
    c.setLineWidth(0.5)
    c.circle(2, 2, 7.5, stroke=1, fill=0)
    draw_flower(c, 2, 2, 4.2, petal=BLUE)
    c.restoreState()


def draw_illuminated_border(c, page_w, page_h, scale=0.92):
    """Full vine-and-gold border for title and part pages."""
    inset_o, inset_i = 26, 31
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.1)
    c.rect(inset_o, inset_o, page_w - 2 * inset_o, page_h - 2 * inset_o,
           stroke=1, fill=0)
    c.setStrokeColor(INK)
    c.setLineWidth(0.4)
    c.rect(inset_i, inset_i, page_w - 2 * inset_i, page_h - 2 * inset_i,
           stroke=1, fill=0)
    m = 46
    draw_corner_vine(c, m, m, 1, 1, scale=scale)
    draw_corner_vine(c, page_w - m, m, -1, 1, scale=scale)
    draw_corner_vine(c, m, page_h - m, 1, -1, scale=scale)
    draw_corner_vine(c, page_w - m, page_h - m, -1, -1, scale=scale)
    # sparse mid-edge sprigs
    for cx, cy, ang in (
        (page_w / 2, page_h - m - 4, 90),
        (page_w / 2, m + 4, -90),
        (m + 4, page_h / 2, 0),
        (page_w - m - 4, page_h / 2, 180),
    ):
        c.saveState()
        c.translate(cx, cy)
        c.rotate(ang)
        draw_leaf(c, 0, 0, 25, 8)
        draw_leaf(c, 0, 0, 155, 8, DEEP_GREEN)
        draw_diamond(c, 0, 0, 2.2)
        c.restoreState()


def draw_body_frame(c, page_w, page_h):
    """Quiet hairline frame with gold corner diamonds for reading pages."""
    inset = 26
    c.setStrokeColor(RULE_GOLD)
    c.setLineWidth(0.45)
    c.rect(inset, inset, page_w - 2 * inset, page_h - 2 * inset,
           stroke=1, fill=0)
    for cx, cy in (
        (inset, inset),
        (page_w - inset, inset),
        (inset, page_h - inset),
        (page_w - inset, page_h - inset),
    ):
        draw_diamond(c, cx, cy, 2.6)


def draw_fleuron(c, x, y, size=7.5, color=GOLD):
    """Small symmetric floral sprig used for scene breaks and seals."""
    c.saveState()
    c.translate(x, y)
    draw_leaf(c, 0, 0, 55, size, GREEN)
    draw_leaf(c, 0, 0, 125, size, DEEP_GREEN)
    draw_leaf(c, 0, 0, -55, size, DEEP_GREEN)
    draw_leaf(c, 0, 0, -125, size, GREEN)
    draw_berry(c, -size * 1.35, 0, 2.3, BLUE)
    draw_berry(c, size * 1.35, 0, 2.3, BLUE)
    draw_flower(c, 0, 0, size * 0.62, petal=CRIMSON, center=color)
    c.restoreState()


def draw_floral_rule(c, x_center, y, width, color=GOLD):
    """Hairline rules flanking a flower-and-leaves cluster."""
    half = width / 2
    c.setStrokeColor(color)
    c.setLineWidth(0.6)
    c.line(x_center - half, y, x_center - 34, y)
    c.line(x_center + 34, y, x_center + half, y)
    draw_leaf(c, x_center - 26, y, 22, 8)
    draw_leaf(c, x_center + 26, y, 158, 8)
    draw_flower(c, x_center, y + 1, 6.2, petal=CRIMSON)
    draw_berry(c, x_center - 15, y, 2.4, BLUE)
    draw_berry(c, x_center + 15, y, 2.4, BLUE)


# ================================================================ flowables
class Display(Flowable):
    """Char-spaced centered display line (manuscript hand feel)."""

    def __init__(self, text, size, color, font="Serif", char_space=2.2,
                 gap=4):
        super().__init__()
        self.text = text
        self.size = size
        self.color = color
        self.font = font
        self.char_space = char_space
        self.height = size + gap
        self.fit_size = size
        self.fit_space = char_space

    def _measure(self, size, space):
        return (
            pdfmetrics.stringWidth(self.text, self.font, size)
            + space * max(0, len(self.text) - 1)
        )

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        size, space = self.size, self.char_space
        while size > 7.5 and self._measure(size, space) > availWidth - 4:
            size -= 0.5
            space = max(0.6, space - 0.15)
        self.fit_size, self.fit_space = size, space
        return availWidth, self.height

    def draw(self):
        c = self.canv
        w = tracked_width(
            c, self.text, self.font, self.fit_size, self.fit_space
        )
        draw_tracked(
            c,
            self.text,
            (self.width - w) / 2 - self.fit_space / 2,
            2,
            self.font,
            self.fit_size,
            self.color,
            self.fit_space,
        )


class FleuronBreak(Flowable):
    def __init__(self, gap=10):
        super().__init__()
        self.gap = gap

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.gap * 2 + 6

    def draw(self):
        draw_fleuron(self.canv, self.width / 2, self.gap + 2, size=7.5)


class FloralRuleFlow(Flowable):
    def __init__(self, width_fraction=0.62, gap=12):
        super().__init__()
        self.fraction = width_fraction
        self.gap = gap

    def wrap(self, availWidth, availHeight):
        self.width = availWidth
        return availWidth, self.gap * 2

    def draw(self):
        draw_floral_rule(
            self.canv, self.width / 2, self.gap, self.width * self.fraction
        )


class IllumInitial(Flowable):
    """Gilded illuminated capital in a crimson/blue square."""

    BOX = 46

    def __init__(self, letter, ground):
        super().__init__()
        self.letter = letter
        self.ground = ground
        self.width = self.BOX + 6
        self.height = self.BOX + 4

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        x, y, s = 2, 2, self.BOX
        c.setFillColor(self.ground)
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.3)
        c.rect(x, y, s, s, stroke=1, fill=1)
        c.setLineWidth(0.5)
        c.rect(x + 3.5, y + 3.5, s - 7, s - 7, stroke=1, fill=0)
        c.setFont("Serif-Bold", 31)
        c.setFillColor(LIGHT_GOLD)
        w = c.stringWidth(self.letter, "Serif-Bold", 31)
        c.drawString(x + (s - w) / 2, y + 8, self.letter)
        # corner sprigs
        draw_leaf(c, x + s - 1, y + s - 1, 30, 7, GREEN)
        draw_leaf(c, x + 1, y + 1, -150, 7, DEEP_GREEN)


class FramedImage(Flowable):
    def __init__(self, path, max_w, max_h):
        super().__init__()
        self.path = str(path)
        ir = ImageReader(self.path)
        iw, ih = ir.getSize()
        scale = min(max_w / iw, max_h / ih)
        self.dw, self.dh = iw * scale, ih * scale

    def wrap(self, availWidth, availHeight):
        return self.dw, self.dh + 8

    def draw(self):
        c = self.canv
        c.drawImage(
            self.path, 0, 4, self.dw, self.dh, preserveAspectRatio=True
        )
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.4)
        c.rect(0, 4, self.dw, self.dh, stroke=1, fill=0)
        c.setStrokeColor(INK)
        c.setLineWidth(0.4)
        c.rect(3.5, 7.5, self.dw - 7, self.dh - 7, stroke=1, fill=0)


# ================================================================ markdown
def md_inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\w)_([^_]+)_(?!\w)", r"<i>\1</i>", text)
    return text


def to_roman(n: int) -> str:
    vals = [
        (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
        (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
        (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
    ]
    out = ""
    for v, sym in vals:
        while n >= v:
            out += sym
            n -= v
    return out


def load_chapter(path: Path):
    lines = path.read_text().splitlines()
    heading = lines[0].lstrip("# ").strip()
    numeral, title = heading.split(" — ", 1)
    blocks, buf = [], []
    for line in lines[1:]:
        if line.strip():
            buf.append(line.strip())
        elif buf:
            blocks.append(" ".join(buf))
            buf = []
    if buf:
        blocks.append(" ".join(buf))
    # collapse any run of consecutive scene breaks into one fleuron
    deduped = []
    for block in blocks:
        if block == "* * *" and deduped and deduped[-1] == "* * *":
            continue
        deduped.append(block)
    return numeral, title, deduped


def chapter_story(numeral, title, blocks, chapter_index):
    story = [
        Spacer(1, 0.42 * inch),
        Display(numeral.upper(), 12.5, GOLD, font="Serif-Bold", char_space=3.4),
        Spacer(1, 6),
        Display(title.upper(), 17.5, CRIMSON, font="Serif-Bold", char_space=2.0),
        FloralRuleFlow(),
        Spacer(1, 14),
    ]
    ground = CRIMSON if chapter_index % 2 == 1 else BLUE
    first_para = blocks[0]
    words = first_para.split()
    initial = words[0][0]
    words[0] = words[0][1:]

    cell_w = PAGE_W - MARGIN_L - MARGIN_R - (IllumInitial.BOX + 8)
    head_lines = []
    line = ""
    idx = 0  # index into words[]; words[0] is the first word minus its capital
    while idx < len(words) and len(head_lines) < 2:
        trial = ((line + " ") + words[idx]).strip()
        if pdfmetrics.stringWidth(trial, "Serif", 10.5) <= cell_w:
            line = trial
            idx += 1
        else:
            head_lines.append(line)
            line = ""
            if len(head_lines) == 2:
                break
    if line and len(head_lines) < 2:
        head_lines.append(line)
    head_text = " ".join(head_lines)
    tail_words = words[idx:]
    drop = Table(
        [
            [
                IllumInitial(initial, ground),
                Paragraph(md_inline(head_text), body_noindent),
            ]
        ],
        colWidths=[IllumInitial.BOX + 8, cell_w],
    )
    drop.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    story.append(drop)
    if tail_words:
        story.append(
            Paragraph(md_inline(" ".join(tail_words)), ParagraphStyle(
                "Tail", parent=body, firstLineIndent=0))
        )
    for block in blocks[1:]:
        if block == "* * *":
            story.append(FleuronBreak())
        else:
            story.append(Paragraph(md_inline(block), body))
    return story


# ================================================================ document
class BookDoc(BaseDocTemplate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_chapter = ""
        self.body_start_physical = None
        self.opener_pages = set()
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
                PageTemplate(id="frontispiece", frames=[frame],
                             onPage=self._plain_page),
                PageTemplate(id="front", frames=[frame],
                             onPage=self._front_page),
                PageTemplate(id="title", frames=[frame],
                             onPage=self._title_page),
                PageTemplate(id="part", frames=[frame],
                             onPage=self._part_page),
                PageTemplate(id="body_opener", frames=[frame],
                             onPage=self._body_page),
                PageTemplate(id="body", frames=[frame],
                             onPage=self._body_page),
            ]
        )

    # ---- page lifecycle
    BODY_TEMPLATES = ("body_opener", "body")

    def handle_pageBegin(self):
        super().handle_pageBegin()
        if (
            self.body_start_physical is None
            and self.pageTemplate.id in self.BODY_TEMPLATES
        ):
            self.body_start_physical = self.page

    def handle_documentBegin(self):
        super().handle_documentBegin()
        # multiBuild reuses this object: purge any template cycle/index
        # armed during the previous pass so it cannot leak into this one
        for attr in (
            "_nextPageTemplateCycle",
            "_nextPageTemplateIndex",
        ):
            if hasattr(self, attr):
                delattr(self, attr)
        self.current_chapter = ""
        self.body_start_physical = None

    def _logical_page(self):
        if self.body_start_physical is None:
            return None
        return self.page - self.body_start_physical + 1

    def _paint_parchment(self, canv):
        canv.setFillColor(PARCHMENT)
        canv.rect(0, 0, PAGE_W, PAGE_H, stroke=0, fill=1)

    def _plain_page(self, canv, doc):
        self._paint_parchment(canv)

    def _front_page(self, canv, doc):
        self._paint_parchment(canv)
        draw_body_frame(canv, PAGE_W, PAGE_H)

    def _title_page(self, canv, doc):
        self._paint_parchment(canv)
        draw_illuminated_border(canv, PAGE_W, PAGE_H)

    def _part_page(self, canv, doc):
        self._paint_parchment(canv)
        draw_illuminated_border(canv, PAGE_W, PAGE_H)

    def _body_page(self, canv, doc):
        # the onPage callback fires before handle_pageBegin, so the first
        # body page establishes the start marker here
        if self.body_start_physical is None:
            self.body_start_physical = self.page
        logical = self._logical_page()
        if logical is None:
            return
        self._paint_parchment(canv)
        draw_body_frame(canv, PAGE_W, PAGE_H)
        canv.saveState()
        # chapter opening pages use the body_opener template: no running
        # head, only the folio
        if self.pageTemplate.id == "body":
            y = PAGE_H - 0.58 * inch
            if logical % 2 == 0:  # verso
                label = "THE LONG SIEGE"
                w = tracked_width(canv, label, "Serif", 8.5, 1.4)
                draw_tracked(canv, label, MARGIN_L, y,
                             "Serif", 8.5, SOFT_INK, 1.4)
            else:  # recto
                label = self.current_chapter.upper()
                w = tracked_width(canv, label, "Serif", 8.5, 1.4)
                draw_tracked(
                    canv, label, PAGE_W - MARGIN_R - w, y,
                    "Serif", 8.5, SOFT_INK, 1.4,
                )
            canv.setStrokeColor(RULE_GOLD)
            canv.setLineWidth(0.5)
            canv.line(MARGIN_L, y - 5, PAGE_W - MARGIN_R, y - 5)
            draw_diamond(canv, PAGE_W / 2, y - 5, 2.0)
        # folio flanked by diamonds
        fy = 0.46 * inch
        canv.setFont("Serif", 9.5)
        canv.setFillColor(INK)
        num = str(logical)
        nw = canv.stringWidth(num, "Serif", 9.5)
        canv.drawCentredString(PAGE_W / 2, fy, num)
        draw_diamond(canv, PAGE_W / 2 - nw / 2 - 9, fy + 3.2, 2.1)
        draw_diamond(canv, PAGE_W / 2 + nw / 2 + 9, fy + 3.2, 2.1)
        canv.restoreState()

    def afterFlowable(self, flowable):
        if flowable.__class__.__name__ == "Display" and getattr(
            flowable, "toc_entry", None
        ):
            self.current_chapter = flowable.toc_title
            # the title lives on the headerless opener page; arm the
            # standard body template for the page that follows
            self.handle_nextPageTemplate("body")
            logical = self._logical_page() or self.page
            self.notify(
                "TOCEntry",
                (0, flowable.toc_entry, logical),
            )


# ================================================================ build
ACTS = [
    (1, "PART THE FIRST", "I",
     ("SUCCESSION AND THE", "FORCED ALLIANCE")),
    (9, "PART THE SECOND", "II",
     ("WAR, REVOLT, AND", "THE SLOW THAW")),
    (18, "PART THE THIRD", "III",
     ("THE SIEGE, THE TRUTH,", "AND THE PRICE OF PEACE")),
]


def part_story(kicker, numeral, name_lines):
    flow = [
        Spacer(1, 1.45 * inch),
        Display(kicker, 13, GOLD, font="Serif-Bold", char_space=3.6),
        Spacer(1, 22),
        Display(numeral, 52, GOLD, font="Serif-Bold", char_space=4, gap=20),
        Spacer(1, 14),
        FloralRuleFlow(width_fraction=0.7),
        Spacer(1, 20),
    ]
    for line in name_lines:
        flow.append(
            Display(line, 13.5, CRIMSON, font="Serif-Bold", char_space=2.4)
        )
        flow.append(Spacer(1, 8))
    flow += [Spacer(1, 26), FleuronBreak()]
    return flow


def build():
    doc = BookDoc(
        str(OUT_PDF),
        pagesize=(PAGE_W, PAGE_H),
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
        title="The Long Siege",
        author="",
    )

    story = []

    # ---- frontispiece
    img = FramedImage(
        ASSETS / "frontispiece.jpg",
        max_w=PAGE_W - MARGIN_L - MARGIN_R - 0.2 * inch,
        max_h=6.3 * inch,
    )
    story.append(Spacer(1, 0.25 * inch))
    story.append(img)
    story.append(NextPageTemplate("front"))
    story.append(PageBreak())

    # ---- half title
    story += [
        Spacer(1, 2.4 * inch),
        Display("THE LONG SIEGE", 24, GOLD, font="Serif-Bold", char_space=3.2),
        FloralRuleFlow(),
        Spacer(1, 10),
        FleuronBreak(),
        NextPageTemplate("title"),
        PageBreak(),
    ]

    # ---- illuminated title page
    story += [
        Spacer(1, 1.15 * inch),
        Display("MCCCCLXXXIV  ·  MCCCCLXXXVI", 10.5, CRIMSON,
                font="Serif-Bold", char_space=2.4),
        Spacer(1, 1.05 * inch),
        Display("THE LONG", 31, GOLD, font="Serif-Bold", char_space=5.5,
                gap=14),
        Display("SIEGE", 31, GOLD, font="Serif-Bold", char_space=7.5, gap=18),
        FloralRuleFlow(width_fraction=0.72),
        Spacer(1, 16),
        Display("A HISTORICAL NOVEL", 12.5, CRIMSON,
                font="Serif-Bold", char_space=3.4),
        Spacer(1, 1.35 * inch),
        FleuronBreak(),
        NextPageTemplate("front"),
        PageBreak(),
    ]

    # ---- copyright / content notice
    story += [
        Spacer(1, 1.7 * inch),
        Paragraph(
            "This is a work of historical fiction. Names, characters, places, "
            "and incidents are the products of the author's imagination or "
            "are used fictitiously. Any resemblance to actual persons, living "
            "or dead, or actual events is entirely coincidental.",
            front_text,
        ),
        Spacer(1, 22),
        FloralRuleFlow(width_fraction=0.5),
        Spacer(1, 18),
        Paragraph(
            "<b>Age rating: Mature / 18+.</b> This novel contains graphic "
            "depictions of warfare and violence and explicit scenes of an "
            "adult nature, written in service of the story. Reader discretion "
            "is advised.",
            front_text,
        ),
        PageBreak(),
    ]

    # ---- contents
    toc = TableOfContents()
    toc.levelStyles = [toc0]
    toc.dotsMinLevel = 0
    story += [
        Spacer(1, 0.35 * inch),
        Display("CONTENTS", 18, CRIMSON, font="Serif-Bold", char_space=4.5),
        FloralRuleFlow(),
        Spacer(1, 16),
        toc,
        NextPageTemplate("part"),
        PageBreak(),
    ]

    # ---- parts and chapters
    act_at = {a[0]: a for a in ACTS}
    for i in range(1, 26):
        if i in act_at:
            _, kicker, numeral, name_lines = act_at[i]
            if i > 1:
                story.append(NextPageTemplate("part"))
                story.append(PageBreak())
            story += part_story(kicker, numeral, name_lines)

        # every chapter starts on a headerless opener page; afterFlowable
        # arms the standard body template once the chapter title is placed
        story.append(NextPageTemplate("body_opener"))
        story.append(PageBreak())

        path = CHAPTERS / f"chapter_{i:04d}.md"
        numeral, title, blocks = load_chapter(path)
        chapter_flow = chapter_story(numeral, title, blocks, i)
        # tag the title Display for the TOC notify
        for fl in chapter_flow:
            if isinstance(fl, Display) and fl.text == title.upper():
                fl.toc_entry = (
                    f'<font color="#B78B2A">{to_roman(i)}.</font>'
                    f"&nbsp;&nbsp;{html.escape(title)}"
                )
                fl.toc_title = title
        story += chapter_flow
        if i == 25:
            story += [
                Spacer(1, 34),
                FloralRuleFlow(width_fraction=0.55),
                Spacer(1, 12),
                Display("FINIS", 15, GOLD, font="Serif-Bold",
                        char_space=5.0),
                Spacer(1, 10),
                FleuronBreak(),
            ]

    doc.multiBuild(story)
    print("wrote", OUT_PDF)


if __name__ == "__main__":
    build()
