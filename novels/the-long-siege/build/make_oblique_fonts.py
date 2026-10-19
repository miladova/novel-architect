"""Generate synthetic oblique TTFs from DejaVu Serif.

DejaVu Serif ships no italic face. We shear the glyf table (0.18 em),
fix bounds/caret metrics, and — critically — give each output font a
UNIQUE internal family/PS name, otherwise ReportLab de-duplicates it
against the regular face and silently never embeds it.
"""
from pathlib import Path

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import GlyphCoordinates

OUT = Path(__file__).parent / "fonts"
OUT.mkdir(exist_ok=True)
SHEAR = 0.18


def make_oblique(src: str, dst: str, family: str, psname: str, subfamily: str):
    f = TTFont(src)
    glyf = f["glyf"]
    for name in glyf.keys():
        g = glyf[name]
        if g.numberOfContours == 0 or g.isComposite():
            continue
        coords, _end_pts, _flags = g.getCoordinates(glyf)
        g.coordinates = GlyphCoordinates(
            [(x + SHEAR * y, y) for x, y in coords]
        )
        g.recalcBounds(glyf)
    f["post"].italicAngle = -10.2
    hhea = f["hhea"]
    hhea.caretSlopeRise = 1000
    hhea.caretSlopeRun = 180
    name = f["name"]
    entries = {
        0: "Synthetic oblique for The Long Siege; DejaVu Fonts license.",
        1: family,
        2: subfamily,
        3: f"{family};synthetic-oblique",
        4: f"{family} {subfamily}",
        5: f"{family} {subfamily}",
        6: psname,
        16: family,
        17: subfamily,
    }
    for nid, val in entries.items():
        name.setName(val, nid, 3, 1, 0x409)
        name.setName(val, nid, 1, 0, 0)
    f.save(dst)
    print("wrote", dst)


SYS = "/usr/share/fonts/truetype/dejavu"
make_oblique(
    f"{SYS}/DejaVuSerif.ttf",
    str(OUT / "DejaVuSerif-Oblique.ttf"),
    "DejaVu Serif Oblique",
    "DejaVuSerif-Oblique",
    "Italic",
)
make_oblique(
    f"{SYS}/DejaVuSerif-Bold.ttf",
    str(OUT / "DejaVuSerif-BoldOblique.ttf"),
    "DejaVu Serif Bold Oblique",
    "DejaVuSerif-BoldOblique",
    "Bold Oblique",
)
