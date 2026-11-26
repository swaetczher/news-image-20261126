#!/usr/bin/env python3
"""news-image-20261126 — one day's world news as a single newspaper page.

Draws a 1024x1024 PNG with the Python standard library only: a 5x7 bitmap
font, a pure-Python PNG encoder, and a declarative TEMPLATE + DATA layout
(anchors + relative positioning, layers background -> content -> foreground).

Run:  python3 main.py            (writes entry.png next to this file, or to
                                   $MAKEFUN_OUTPUT_DIR/entry.png when set)
Variant (local exploration only; the grader runs the default): set the
NEWS_VARIANT environment variable to A, B or C. Default is B, the winner of
the pairwise round documented in produksi.md.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Design system — recipe: monocle-magazine (fixed for this edition)
# ---------------------------------------------------------------------------
# Paper cream, ink black, ONE editorial red accent, hairline rules, square
# corners (radius 0). Hierarchy: kicker -> headline -> dek -> fact strip.
# Headline scale is >= 2.5x body scale in every variant.
PAPER = (242, 239, 231)      # #F2EFE7
INK = (26, 26, 26)           # #1A1A1A
ACCENT = (199, 50, 46)       # #C7322E — the single accent colour
HAIRLINE = (200, 194, 176)   # #C8C2B0
MUTED = (90, 86, 76)         # warm grey for the footer only

W, H = 1024, 1024
MARGIN = 40
CONTENT_W = W - 2 * MARGIN   # 944

# Which variant to render. B won the pairwise round (see produksi.md).
VARIANT = os.environ.get("NEWS_VARIANT", "B").strip().upper() or "B"

# ---------------------------------------------------------------------------
# 5x7 bitmap font (uppercase ASCII + digits + punctuation). Each glyph is
# 7 rows of 5 bits, '#' = ink, '.' = empty. Drawn by hand for this entry.
# ---------------------------------------------------------------------------
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
}

CHAR_ADVANCE = 6  # 5 px glyph + 1 px tracking, times the scale


def text_width(text, scale):
    return len(text) * CHAR_ADVANCE * scale - scale


def wrap_text(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    max_chars = max(1, (max_width + scale) // (CHAR_ADVANCE * scale))
    lines, current = [], ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if len(trial) <= max_chars:
            current = trial
        else:
            if current:
                lines.append(current)
            # A single over-long word is hard-split (never overflows).
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# DATA — the edition: 5 stories + 1 reserve, verified from Reuters / CNN / AP
# (see riset.md). Dates follow the research notes: the Huawei verdict is
# 24 Nov, the rest was reported 25 Nov; the Houthi refinery strike is a
# CLAIM, not a Saudi-confirmed fact; Cairo toll is 31 dead, 21 injured.
# ---------------------------------------------------------------------------
DATA = {
    "masthead": "THE WORLD IN ONE PAGE",
    "dateline": "THURSDAY 26 NOVEMBER 2026",
    "dateline_sub": "FIVE STORIES THAT MOVED THE WORLD",
    "hero": {
        "kicker": "TRADE - SECTION 301",
        "headline": "US PROPOSES NEW TARIFFS ON 14 TRADING PARTNERS",
        "dek": "Washington moves against what it calls structural excess factory "
               "capacity. China faces the highest rate at 20 percent, with Vietnam "
               "also at 20 percent. Mexico and Norway are spared for now.",
        "fact": "14 NATIONS - CHINA 20% - VIETNAM 20% - CAP 15% FOR EU, JAPAN, SOUTH KOREA",
    },
    "grid": [
        {
            "kicker": "TECH - US COURT",
            "headline": "HUAWEI CONVICTED IN US TRADE-SECRETS TRIAL",
            "dek": "A Brooklyn jury finds the firm guilty on 10 of 12 counts, including "
                   "trade-secret theft and Iran sanctions breaches. It clears Huawei of "
                   "racketeering. Verdict: 24 Nov.",
            "fact": "SENTENCING: 14 SEP 2027 - FINES COULD RUN TO BILLIONS",
        },
        {
            "kicker": "MIDDLE EAST - YEMEN",
            "headline": "HOUTHIS CLAIM STRIKE ON SAUDI OIL REFINERY",
            "dek": "The group says it hit the Ras Tanura refinery; US crude rose 1.8 "
                   "percent to $83.52. A drone also struck Riyadh's tallest tower for "
                   "the second time in a week, injuring 11.",
            "fact": "7,000+ MISSILES AND DRONES FIRED AT GULF STATES SINCE FEB",
        },
        {
            "kicker": "SPACE - CHINA",
            "headline": "PAKISTAN'S FIRST ASTRONAUT REACHES ORBIT",
            "dek": "Muhammad Zeeshan Ali joins China's Tiangong station aboard "
                   "Shenzhou-24, launched 25 Nov. The crew will run more than 90 "
                   "science experiments.",
            "fact": "CREW: TANG HONGBO, WU YI, ZEESHAN ALI - STAY: 5 TO 10 DAYS",
        },
        {
            "kicker": "EGYPT - DISASTER",
            "headline": "CAIRO TANKER FIRE KILLS 31",
            "dek": "A fuel tanker crash on the Ring Road in Giza sets off a blaze that "
                   "destroys 27 vehicles. Health officials report 31 dead and 21 "
                   "injured; 39 ambulances sent.",
            "fact": "27 VEHICLES DESTROYED - CAUSE STILL UNKNOWN",
        },
    ],
    "footer": "SOURCES: REUTERS, CNN, AP - REPORTS OF 25 NOV 2026. THE HOUTHI "
              "REFINERY STRIKE IS REPORTED AS A CLAIM, NOT CONFIRMED BY SAUDI ARABIA.",
}

# ---------------------------------------------------------------------------
# TEMPLATE — one layout, three hierarchy/spacing variants of the SAME recipe.
# Variant A: balanced hero (headline 4x), roomy grid. Variant B: dominant
# hero (headline 5x) + red fact strip. Variant C: quiet hero (headline 4x),
# smaller grid headlines (2x) with longer deks.
# ---------------------------------------------------------------------------
TEMPLATE = {
    "size": (W, H),
    "margin": MARGIN,
    "layers": ["background", "content", "foreground"],
    "variants": {
        "A": {"hero_head": 4, "hero_dek": 2, "grid_head": 3, "grid_dek": 2,
              "gutter": 28, "hero_pad": 26, "fact_strip": False},
        "B": {"hero_head": 5, "hero_dek": 2, "grid_head": 3, "grid_dek": 2,
              "gutter": 24, "hero_pad": 22, "fact_strip": True},
        "C": {"hero_head": 4, "hero_dek": 2, "grid_head": 2, "grid_dek": 2,
              "gutter": 28, "hero_pad": 26, "fact_strip": False},
    },
}


class Canvas:
    """An RGB pixel buffer with rect / text drawing primitives."""

    def __init__(self, w, h, colour):
        self.w, self.h = w, h
        self.px = bytearray(colour * (w * h))

    def rect(self, x, y, w, h, colour):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        r, g, b = colour
        row = bytes((r, g, b)) * (x1 - x0)
        for yy in range(y0, y1):
            off = (yy * self.w + x0) * 3
            self.px[off:off + len(row)] = row

    def hline(self, x, y, w, colour, thick=1):
        self.rect(x, y, w, thick, colour)

    def text(self, x, y, s, colour, scale):
        """Draw one line of text; returns the x just past the last glyph."""
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, FONT[" "])
            for row_i, row in enumerate(glyph):
                for col_i, bit in enumerate(row):
                    if bit == "1":
                        self.rect(cx + col_i * scale, y + row_i * scale,
                                  scale, scale, colour)
            cx += CHAR_ADVANCE * scale
        return cx

    def text_centered(self, y, s, colour, scale):
        x = (self.w - text_width(s, scale)) // 2
        return self.text(x, y, s, colour, scale)

    def paragraph(self, x, y, s, colour, scale, max_width, line_gap=4):
        """Draw wrapped text; returns the y just below the last line."""
        line_h = 7 * scale + line_gap
        for line in wrap_text(s, scale, max_width):
            self.text(x, y, line, colour, scale)
            y += line_h
        return y


# Anchor helpers (relative positioning — no hard-coded absolute coordinates
# inside the layout body; every block starts below() the previous anchor).
def below(anchor_y, gap):
    return anchor_y + gap


def encode_png(canvas):
    """Deterministic PNG: filter 0 on every scanline, fixed zlib level."""
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)
        raw.extend(canvas.px[y * stride:(y + 1) * stride])
    comp = zlib.compress(bytes(raw), 6)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", comp) + chunk(b"IEND", b""))


def render(variant):
    cfg = TEMPLATE["variants"][variant]
    cv = Canvas(W, H, PAPER)
    anchors = {}

    # ---- layer: background (paper + outer frame) ----
    cv.rect(0, 0, W, H, PAPER)
    cv.rect(16, 16, W - 32, H - 32, PAPER)
    cv.hline(16, 16, W - 32, INK, 3)
    cv.hline(16, H - 19, W - 32, INK, 3)

    # ---- layer: content — masthead ----
    y = 44
    cv.text_centered(y, DATA["masthead"], INK, 6)
    anchors["masthead_bottom"] = y + 7 * 6
    y = below(anchors["masthead_bottom"], 14)
    cv.hline(MARGIN, y, CONTENT_W, ACCENT, 4)
    anchors["rule_top"] = y
    y = below(y, 12)
    cv.text_centered(y, DATA["dateline"], ACCENT, 2)
    y = below(y, 7 * 2 + 6)
    cv.text_centered(y, DATA["dateline_sub"], INK, 2)
    anchors["dateline_bottom"] = y + 7 * 2
    y = below(anchors["dateline_bottom"], 12)
    cv.hline(MARGIN, y, CONTENT_W, HAIRLINE, 2)
    anchors["masthead_rule"] = y

    # ---- layer: content — hero (editorial-cover block) ----
    y = below(anchors["masthead_rule"], cfg["hero_pad"])
    hero = DATA["hero"]
    cv.text(MARGIN, y, hero["kicker"], ACCENT, 2)
    y = below(y, 7 * 2 + 10)
    y = cv.paragraph(MARGIN, y, hero["headline"], INK, cfg["hero_head"],
                     CONTENT_W, line_gap=6)
    y = below(y, 10)
    y = cv.paragraph(MARGIN, y, hero["dek"], INK, cfg["hero_dek"],
                     CONTENT_W, line_gap=5)
    if cfg["fact_strip"]:
        y = below(y, 12)
        cv.rect(MARGIN, y, CONTENT_W, 7 * 2 + 16, ACCENT)
        cv.text(MARGIN + 14, y + 8, hero["fact"], PAPER, 2)
        y = below(y, 7 * 2 + 16)
    anchors["hero_bottom"] = y
    y = below(anchors["hero_bottom"], 14)
    cv.hline(MARGIN, y, CONTENT_W, INK, 3)
    anchors["hero_rule"] = y

    # ---- layer: content — banner-grid-2x2 ----
    gutter = cfg["gutter"]
    col_w = (CONTENT_W - gutter) // 2
    grid_top = below(anchors["hero_rule"], 18)
    row_h = (H - 40 - grid_top - 60) // 2  # leaves room for the footer
    for idx, story in enumerate(DATA["grid"]):
        col = idx % 2
        row = idx // 2
        gx = MARGIN + col * (col_w + gutter)
        gy = grid_top + row * row_h
        if col == 1:
            cv.rect(gx - gutter // 2, gy, 2, row_h - 16, HAIRLINE)
        if row == 1:
            cv.rect(MARGIN, gy - 12, CONTENT_W, 2, HAIRLINE)
        yy = gy
        cv.text(gx, yy, story["kicker"], ACCENT, 2)
        yy = below(yy, 7 * 2 + 8)
        yy = cv.paragraph(gx, yy, story["headline"], INK, cfg["grid_head"],
                          col_w, line_gap=5)
        yy = below(yy, 8)
        yy = cv.paragraph(gx, yy, story["dek"], INK, cfg["grid_dek"], col_w,
                          line_gap=4)
        # Fact strip: one short verified figure per panel, in the accent
        # colour — the single CoHP refinement of the winning variant.
        yy = below(yy, 10)
        cv.paragraph(gx, yy, story["fact"], ACCENT, 2, col_w, line_gap=4)
    anchors["grid_bottom"] = grid_top + 2 * row_h

    # ---- layer: foreground — footer ----
    fy = H - 40 - 7 * 2 - 8
    cv.hline(MARGIN, fy - 12, CONTENT_W, HAIRLINE, 2)
    f_lines = wrap_text(DATA["footer"], 2, CONTENT_W)
    cv.text(MARGIN, fy, f_lines[0], MUTED, 2)
    if len(f_lines) > 1:
        cv.text(MARGIN, fy + 7 * 2 + 4, f_lines[1], MUTED, 2)
    return encode_png(cv)


def main():
    variant = VARIANT if VARIANT in TEMPLATE["variants"] else "B"
    png = render(variant)
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    try:
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "entry.png")
    except OSError:
        path = "entry.png"
    with open(path, "wb") as f:
        f.write(png)
    print("wrote %s (%d bytes, variant %s)" % (path, len(png), variant))


if __name__ == "__main__":
    main()
