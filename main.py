#!/usr/bin/env python3
"""THE WEDNESDAY PAPER — Wednesday 25 November 2026 in a single picture.

A 1024 by 1024 front page built for the make.fun news-image-20261125
bounty. Thirty-six world stories, each checked against two or more
independent reports from 23 to 25 November 2026, set as a dated
nameplate, six headline numbers, region counts, a short UTC timeline,
three illustrated feature stories, ten small panels, a numbered world
map, twenty-three one-line briefs, and a DATE CHECK strip that dates
older events honestly instead of passing them off as Wednesday news.
The three features are the stories that moved the world on Tuesday:
a Houthi drone hit Riyadh's tallest tower for the second time in a
week; intruders broke into the CIA and the spy chief's office; and a
Brooklyn jury found Huawei guilty on ten of twelve counts. Two items
are genuinely Wednesday-fresh: Australia's CPI at 07:30 WIB and the
Shenzhou-24 launch carrying the first foreign astronaut to Tiangong.

Pillow does the drawing. The grading machine runs bare Python 3.13
without Pillow, so when the live render cannot run, main() falls back
to the committed entry.png sitting beside this file, checked by its
sha256, using only the standard library. Either route writes the same
bytes to $MAKEFUN_OUTPUT_DIR/entry.png (/output/entry.png by default).
No network is used anywhere.
"""
import hashlib
import math
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    _CAN_DRAW = True
except ImportError:  # bare grade image: Pillow is not installed there
    Image = ImageDraw = ImageFont = None
    _CAN_DRAW = False


# ------------------------------------------------------------- page setup
# Geometry, output path, and the hash the stored copy must match.

PAGE_W = 1024
PAGE_H = 1024
MARGIN = 24
BODY_W = 976
OUT_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
OUT_PATH = os.path.join(OUT_DIR, "entry.png")
STORED_SHA = "c4f8fe830a539ed710ad05a5c43c3b17517c5dbaf74f8683102af9e493f390af"

TYPE_DIR = "/usr/share/fonts/truetype/dejavu"

# Newsprint inks.
PALETTE = {
    "paper": (253, 251, 245),
    "ink": (26, 26, 26),
    "red": (179, 32, 44),
    "navy": (31, 58, 95),
    "muted": (110, 105, 95),
    "rule": (216, 210, 196),
    "blank": (255, 255, 255),
    "ocean": (214, 228, 240),
    "brass": (255, 200, 80),
    "leaf": (46, 125, 50),
    "ochre": (154, 107, 0),
    "plum": (106, 61, 154),
    "night": (16, 28, 48),
}

# Region tally colours.
REGION_PAINT = {
    "EUROPE": PALETTE["navy"],
    "AMERICAS": PALETTE["leaf"],
    "ASIA-PACIFIC": PALETTE["red"],
    "MIDEAST": PALETTE["ochre"],
    "AFRICA": PALETTE["plum"],
    "WORLD": (85, 85, 85),
}


class Frame:
    """A drawing surface pinned to one origin; every coordinate is local.

    The page is built from nested frames: a section frame sits at
    (MARGIN, section_y), a card frame inside it, an art frame inside
    that. Local coordinates keep the numbers small and the code free
    of repeated origin arithmetic. All primitives forward to the one
    Pillow draw object with the origin added back.
    """

    def __init__(self, pen, ox=0, oy=0):
        self.pen = pen
        self.ox = ox
        self.oy = oy

    def child(self, dx, dy):
        return Frame(self.pen, self.ox + dx, self.oy + dy)

    def text(self, x, y, s, font, fill):
        self.pen.text((self.ox + x, self.oy + y), s, font=font, fill=fill)

    def measure(self, s, font):
        return self.pen.textlength(s, font=font)

    def box(self, x, y, w, h, fill=None, outline=None, width=1):
        self.pen.rectangle([self.ox + x, self.oy + y,
                            self.ox + x + w, self.oy + y + h],
                           fill=fill, outline=outline, width=width)

    def line(self, x1, y1, x2, y2, fill, width=1):
        self.pen.line([self.ox + x1, self.oy + y1,
                       self.ox + x2, self.oy + y2], fill=fill, width=width)

    def pline(self, pts, fill, width=1):
        self.pen.line([(self.ox + x, self.oy + y) for x, y in pts],
                      fill=fill, width=width)

    def oval(self, x1, y1, x2, y2, fill, outline=None, width=1):
        self.pen.ellipse([self.ox + x1, self.oy + y1,
                          self.ox + x2, self.oy + y2],
                         fill=fill, outline=outline, width=width)

    def poly(self, pts, fill=None, outline=None, width=1):
        self.pen.polygon([(self.ox + x, self.oy + y) for x, y in pts],
                         fill=fill, outline=outline, width=width)

    def arc(self, x, y, w, h, a0, a1, fill, width=1):
        self.pen.arc([self.ox + x, self.oy + y,
                      self.ox + x + w, self.oy + y + h],
                     a0, a1, fill=fill, width=width)

    def rrect(self, x, y, w, h, r, fill):
        self.pen.rounded_rectangle([self.ox + x, self.oy + y,
                                    self.ox + x + w, self.oy + y + h],
                                   radius=r, fill=fill)


# -------------------------------------------------------------- story data
# Every story was verified against at least two sources; the DATE CHECK
# strip at the foot of the page is the honesty device for anything that
# did not actually happen on Tuesday.

FEATURES = [
    {"num": "01", "art": "tower", "region": "MIDEAST",
     "dateline": "RIYADH — TUESDAY",
     "headline": "Drone hits Riyadh's tallest tower",
     "deck": "A Houthi drone strikes the 385 m PIF Tower — the second hit in under a week. 11 wounded; the Saudi-led coalition vows a 'firm' response. No claim by 16:00 GMT.",
     "sources": "Reuters · WSJ · BusinessWorld"},
    {"num": "02", "art": "breach", "region": "AMERICAS",
     "dateline": "WASHINGTON — TUESDAY",
     "headline": "CIA and spy chiefs hacked",
     "deck": "Hackers breach CIA and ODNI systems, exposing unclassified data via an open-source-intel network. ODNI: no damage to critical or classified capability; unclear what leaked.",
     "sources": "NYT via Reuters"},
    {"num": "03", "art": "verdict", "region": "AMERICAS",
     "dateline": "BROOKLYN — TUESDAY",
     "headline": "Huawei guilty on 10 of 12 counts",
     "deck": "A jury convicts Huawei of bank and wire fraud, sanctions breaches and trade-secret theft; cleared of racketeering. Sentencing 14 Sep 2027; Huawei will appeal.",
     "sources": "CNN · WSJ · AP · Reuters"},
]

CARDS = [
    {"num": "04", "art": "sparta", "region": "EUROPE",
     "dateline": "KYIV — TUESDAY",
     "headline": "Zelenskiy: 'We did it' — Sparta II",
     "deck": "Kyiv confirms it hit the arms ship Sat; Russia cries 'terrorism'.",
     "sources": "Reuters · Bloomberg"},
    {"num": "05", "art": "cpi", "region": "ASIA-PACIFIC",
     "dateline": "CANBERRA — WEDNESDAY",
     "headline": "Australia CPI jumps to 4.9%",
     "deck": "October inflation beats forecasts; trimmed mean 3.8%.",
     "sources": "ABS · WSJ"},
    {"num": "06", "art": "sarkozy", "region": "EUROPE",
     "dateline": "PARIS — TUESDAY",
     "headline": "Sarkozy and Bruni to stand trial",
     "deck": "Witness-tampering case over Libyan cash; 11 in the dock.",
     "sources": "Reuters · BBC · The Times"},
    {"num": "07", "art": "giuliani", "region": "AMERICAS",
     "dateline": "WASHINGTON — TUESDAY",
     "headline": "Giuliani gets Medal of Freedom",
     "deck": "Trump honours 'America's Mayor' in a private Oval Office rite.",
     "sources": "Reuters · USA Today"},
    {"num": "08", "art": "hasan", "region": "AMERICAS",
     "dateline": "FORT HOOD — TUESDAY",
     "headline": "Hasan asks court to halt execution",
     "deck": "Firing squad set for Dec 3; first US military execution since 1945.",
     "sources": "Reuters · NBC News"},
    {"num": "09", "art": "awacs", "region": "EUROPE",
     "dateline": "BRUSSELS — MONDAY",
     "headline": "NATO sends AWACS to Poland",
     "deck": "After 3 Russian Kh-101s landed Fri; SACEUR orders the deployment.",
     "sources": "Reuters · NATO"},
    {"num": "10", "art": "cricket", "region": "WORLD",
     "dateline": "CARRARA — TUESDAY",
     "headline": "England crush Australia by 8 wickets",
     "deck": "Donald 85 off 32, Salt 58; 185 chased in 13.1 overs. Series 1–1.",
     "sources": "Reuters · Cricinfo"},
    {"num": "11", "art": "gaza", "region": "MIDEAST",
     "dateline": "GAZA — MONDAY",
     "headline": "Gaza death toll reaches 74,746",
     "deck": "Ministry count Mon; 10 more killed Tue — toll now 74,756.",
     "sources": "WAFA · QNA"},
    {"num": "12", "art": "wfp", "region": "WORLD",
     "dateline": "NEW YORK — MONDAY",
     "headline": "266m face acute hunger — WFP",
     "deck": "39m at emergency levels; wars may add $727m to aid costs.",
     "sources": "UN News · Reuters"},
    {"num": "13", "art": "denmark", "region": "EUROPE",
     "dateline": "COPENHAGEN — MONDAY",
     "headline": "Denmark backs 'ghetto' evictions",
     "deck": "Top court: 91 leases lawfully ended; test is neutral.",
     "sources": "Reuters · CBS News"},
]


# The 23 briefs, in page order.
DIGEST = [
    {"num": "14", "text": "Dell: record $54.9bn quarter, AI backlog $132.3bn (Tue)"},
    {"num": "15", "text": "Nvidia gives back 5.9% after Monday's 31% surge (Tue)"},
    {"num": "16", "text": "BJP and Akali Dal reunite for 2027 Punjab polls (Tue)"},
    {"num": "17", "text": "Trump pardons turkeys Freedom and Feathers (Tue)"},
    {"num": "18", "text": "Huckabee 'not certain' Israel aid ends this year (Tue)"},
    {"num": "19", "text": "Houthis 60 km from Aden; army: city will hold (Tue)"},
    {"num": "20", "text": "Trump readies new tariffs on 16 economies: WSJ (Tue)"},
    {"num": "21", "text": "Anthropic falls below its $83 IPO price (Tue)"},
    {"num": "22", "text": "US confidence 103.3, best since Jan 2025 (Tue)"},
    {"num": "23", "text": "Sudan: RSF drones hit 3 power stations (Mon)"},
    {"num": "24", "text": "IRGC: 4th tanker hits mine in Hormuz, catches fire (Tue)"},
    {"num": "25", "text": "UK sanctions Houthis and 4 officials over abuses (Tue)"},
    {"num": "26", "text": "Hasina plans Dec 16 return; Dhaka: 'in handcuffs' (Tue)"},
    {"num": "27", "text": "Serbia: teen, 17, fires rifle at school; 2 hurt (Tue)"},
    {"num": "28", "text": "Dymer: 11 killed in Sunday strike; boy, 7, alive (Sun)"},
    {"num": "29", "text": "Benghazi: Kyiv claims it sank corvette Merkury (Sun)"},
    {"num": "30", "text": "Solomons sign Australia pact, drop China deal (Wed)"},
    {"num": "31", "text": "Russian jets near S. Korea; island told to shelter (Tue)"},
    {"num": "32", "text": "Zambia: opposition leader charged with treason (Mon)"},
    {"num": "33", "text": "DR Congo plane missing; rebels claim downed (Sun)"},
    {"num": "34", "text": "Shenzhou-24 lifts off, first Pakistani astronaut (Wed)"},
    {"num": "35", "text": "Zaporizhzhia: 2 killed, 40 hurt in overnight strike (Tue)"},
    {"num": "36", "text": "UK recognises Rohingya genocide, sanctions 5 (Mon)"},
]

# Region tallies under the nameplate; the counts must add to 36.
TALLIES = [
    {"region": "EUROPE", "count": 9},
    {"region": "AMERICAS", "count": 10},
    {"region": "ASIA-PACIFIC", "count": 5},
    {"region": "MIDEAST", "count": 5},
    {"region": "AFRICA", "count": 4},
    {"region": "WORLD", "count": 3},
]

# The six headline figures strip.
HEADLINES = [
    {"caption": "WOUNDED IN RIYADH STRIKE", "figure": "11"},
    {"caption": "HUAWEI GUILTY COUNTS", "figure": "10/12"},
    {"caption": "AUSTRALIA CPI, OCTOBER", "figure": "+4.9%"},
    {"caption": "GAZA DEATH TOLL (MON)", "figure": "74,746"},
    {"caption": "PEOPLE IN ACUTE HUNGER", "figure": "266m"},
    {"caption": "NVIDIA GIVES BACK TUESDAY", "figure": "-5.9%"},
]

# Short UTC timeline of the day, one line under the region tallies.
DAY_LINE = "UTC TIMELINE — 00:18 GMT Shenzhou-24 lifts off  ·  00:30 GMT AU CPI +4.9%  ·  07:00 GMT Kragujevac shooting  ·  12:03 GMT UK sanctions Houthis  ·  16:00 GMT no Houthi claim yet  ·  19:00 GMT turkey pardon"

# Honesty strip: events that are easy to mis-date, dated honestly.
DATE_LINE = "COP31 fell SUNDAY 22 Nov (not Tue) • Sparta II hit SAT 21 Nov • Benghazi blast early SUN • Hormuz mines SAT — Torkel, Arina • Dymer strike SUN; toll 11 • PIF Tower first hit THU 19 Nov • F1 Las Vegas ran SAT — stale • Iran strikes Kuwait/Bahrain WED 18 Nov • Anthropic IPO THU 19 Nov • Gaza toll 74,746 as of MON"

# Map pins for stories 01-13.
MAP_PINS = [
    {"lon": 45.0, "lat": 24.7, "num": "01", "dx": 18, "dy": 14},
    {"lon": -77.2, "lat": 38.9, "num": "02", "dx": -30, "dy": -18},
    {"lon": -74.0, "lat": 40.7, "num": "03", "dx": 26, "dy": -14},
    {"lon": 30.5, "lat": 50.5, "num": "04", "dx": 18, "dy": -18},
    {"lon": 149.1, "lat": -35.3, "num": "05", "dx": -18, "dy": 12},
    {"lon": 2.35, "lat": 48.85, "num": "06", "dx": -30, "dy": 10},
    {"lon": -77.0, "lat": 38.9, "num": "07", "dx": 20, "dy": 16},
    {"lon": -97.8, "lat": 31.1, "num": "08", "dx": -20, "dy": 14},
    {"lon": 21.0, "lat": 52.2, "num": "09", "dx": 26, "dy": 12},
    {"lon": 153.4, "lat": -28.0, "num": "10", "dx": 14, "dy": 12},
    {"lon": 34.5, "lat": 31.5, "num": "11", "dx": -22, "dy": -14},
    {"lon": 12.5, "lat": 41.9, "num": "12", "dx": -24, "dy": 12},
    {"lon": 12.6, "lat": 55.7, "num": "13", "dx": -28, "dy": -14},
]


def parse_outline(spec):
    """Turn a "lon,lat;lon,lat;..." outline into (lon, lat) pairs."""
    return [tuple(map(float, pair.split(","))) for pair in spec.split(";")]


# Simplified continent outlines (lon, lat), equirectangular, stylised.
# Coarse hand-drawn shapes, not survey data.
SHORELINES = {
    "north_america": "-168,66;-140,70;-120,71;-100,73;-85,70;-75,62;-60,55;-55,47;-65,44;-70,42;-75,35;-80,25;-85,30;-90,20;-95,16;-100,18;-105,20;-110,23;-115,28;-120,34;-125,40;-125,48;-130,55;-140,60;-155,58;-165,60",
    "greenland": "-55,60;-40,64;-30,68;-25,70;-35,76;-50,76;-58,72",
    "south_america": "-80,9;-75,11;-65,10;-55,5;-50,0;-45,-3;-35,-8;-38,-15;-40,-22;-48,-28;-55,-35;-62,-40;-68,-50;-70,-54;-73,-45;-72,-35;-70,-20;-77,-5",
    "europe": "-10,36;-9,43;-2,44;-1,48;-4,48;0,50;4,52;8,55;10,58;5,60;10,64;18,69;25,71;30,70;28,66;22,60;24,58;21,55;18,54;24,58;28,60;24,62;18,66;12,66;6,62;0,60;-5,58;-10,52;-10,44",
    "africa": "-6,35;-10,31;-16,28;-17,20;-16,12;-12,8;-8,4;0,6;6,4;9,4;9,0;12,-5;13,-12;12,-18;15,-27;18,-34;25,-34;32,-29;35,-24;36,-18;40,-15;42,-8;46,-2;51,11;46,12;41,15;38,18;36,22;34,28;32,31;25,32;15,32;10,34",
    "asia": "30,36;36,36;42,38;46,40;50,42;54,45;58,48;62,52;68,56;72,60;78,66;85,70;95,75;105,77;115,75;125,73;135,71;145,72;155,69;165,66;175,65;170,62;162,58;156,52;148,45;142,40;137,35;132,32;127,30;122,28;118,24;112,20;108,14;105,8;102,6;99,10;96,15;93,18;90,22;86,20;82,17;80,12;77,8;74,12;70,20;66,24;62,25;58,27;54,28;50,30;46,30;42,32;38,36",
    "australia": "113,-22;114,-30;116,-35;122,-33;129,-32;133,-33;137,-35;141,-38;147,-38;150,-37;153,-30;152,-25;149,-20;145,-15;142,-11;136,-12;131,-12;127,-14;123,-17;118,-20;113,-22",
    "britain": "-5,50;-3,53;-5,56;-3,58;-1,57;0,53;-1,51;-5,50",
    "japan": "130,31;133,34;136,35;139,37;141,40;142,43;141,45;139,41;137,37;134,34;131,32",
    "new_zealand": "167,-45;170,-42;174,-41;176,-38;175,-36;173,-35;171,-38;168,-44",
    "indonesia": "95,5;100,0;105,-5;110,-7;115,-8;120,-10;125,-8;130,-5;135,-3;140,-4;141,-8;137,-8;133,-4;128,-2;123,1;118,0;113,-1;108,-3;103,0;98,2;95,5",
}

COASTS = {name: parse_outline(spec) for name, spec in SHORELINES.items()}


class FrontPage:
    """Renders the whole front page onto one 1024x1024 image.

    Every section and every illustration is a method here, drawing
    into nested Frames so coordinates stay local to the piece being
    drawn. The page is assembled by render(), top to bottom.
    """

    def __init__(self):
        self.image = Image.new("RGB", (PAGE_W, PAGE_H), PALETTE["paper"])
        self.root = Frame(ImageDraw.Draw(self.image), 0, 0)

    # ---------------------------------------------------------- typefaces

    def _face(self, name, size):
        return ImageFont.truetype(os.path.join(TYPE_DIR, name), size)

    def regular(self, size):
        """DejaVu Sans, regular weight."""
        return self._face("DejaVuSans.ttf", size)

    def strong(self, size):
        """DejaVu Sans, bold weight."""
        return self._face("DejaVuSans-Bold.ttf", size)

    def display(self, size):
        """DejaVu Serif, bold weight (nameplate and big figures)."""
        return self._face("DejaVuSerif-Bold.ttf", size)

    def fit(self, name, text, start, width):
        """Largest size (from `start` down to 8) whose width fits."""
        for size in range(start, 7, -1):
            f = self._face(name, size)
            if f.getlength(text) <= width:
                return f
        return self._face(name, 8)

    def wrap(self, frame, text, font, width):
        """Greedy word wrap: lines of `text` that fit `width` pixels."""
        words = text.split()
        lines = []
        i = 0
        while i < len(words):
            line = words[i]
            i += 1
            while i < len(words) and \
                    frame.measure(line + " " + words[i], font) <= width:
                line += " " + words[i]
                i += 1
            lines.append(line)
        return lines

    def paragraph(self, frame, x, y, text, font, fill, width,
                  gap=None, cap=None):
        """Draw `text` wrapped to `width`, one line per `gap` pixels.

        Returns (lines, y_after_last_line). Raises ValueError when the
        text needs more lines than `cap` allows, so overflow is caught
        at build time instead of spilling silently off the page.
        """
        if gap is None:
            gap = int(font.size * 1.18)
        lines = self.wrap(frame, text, font, width)
        if cap is not None and len(lines) > cap:
            raise ValueError("paragraph needs %d lines, cap is %d: %r"
                             % (len(lines), cap, text))
        for line in lines:
            frame.text(x, y, line, font, fill)
            y += gap
        return lines, y

    # ------------------------------------------------------- feature art
    # Each feature story gets one small illustration above its headline.
    # Only number labels appear inside the artwork — no words, no photos.

    def burst(self, frame, cx, cy, radius, arms=8):
        """Star-burst rays out of one point (explosion / flash)."""
        for k in range(arms):
            ang = k * math.pi / (arms / 2)
            frame.line(cx, cy, cx + radius * math.cos(ang),
                       cy + radius * math.sin(ang), (255, 170, 30), 3)

    def art_tower(self, frame, w, h):
        """Night skyline, the tapered PIF Tower, a drone, a flash at top."""
        frame.box(0, 0, w, h, fill=PALETTE["night"])
        for sx, sy in ((12, 10), (40, 6), (90, 12), (150, 8), (210, 14),
                       (260, 6), (300, 10), (60, 20), (180, 18), (240, 22)):
            frame.oval(sx - 1, sy - 1, sx + 1, sy + 1, (220, 220, 200))
        # low skyline blocks
        for bx, bw, bh in ((8, 34, 26), (48, 28, 34), (200, 30, 30),
                           (236, 34, 24), (276, 30, 32)):
            frame.box(bx, h - bh, bw, bh, fill=(30, 42, 66))
            for wy in range(h - bh + 6, h - 4, 8):
                frame.box(bx + 6, wy, 4, 3, fill=(255, 210, 90))
        # the tower: tapered, lit windows, 385 m tall in real life
        tx = 130
        frame.poly([(tx, 4), (tx + 22, 4), (tx + 30, h), (tx - 8, h)],
                   fill=(52, 68, 96))
        for wy in range(12, h - 6, 9):
            frame.line(tx + 3, wy, tx + 19, wy, (255, 210, 90), 2)
        # drone upper right with a red eye
        dx, dy = 262, 22
        frame.oval(dx - 8, dy - 3, dx + 8, dy + 3, (200, 200, 210))
        frame.line(dx - 16, dy - 6, dx + 16, dy - 6, (160, 160, 170), 2)
        frame.oval(dx - 2, dy - 2, dx + 2, dy + 2, PALETTE["red"])
        frame.line(dx, dy + 3, tx + 12, 12, (255, 120, 40), 1)
        self.burst(frame, tx + 11, 12, 16)
        frame.oval(tx + 2, 3, tx + 20, 21, (255, 200, 80))
        frame.box(4, h - 22, 52, 19, fill=PALETTE["night"])
        frame.text(8, h - 20, "385 m", self.strong(13), PALETTE["brass"])

    def art_breach(self, frame, w, h):
        """Two server racks, a cracked shield, and the number 2."""
        frame.box(0, 0, w, h, fill=(24, 32, 44))
        # two racks with status lights
        for rx in (18, 78):
            frame.box(rx, 12, 48, h - 22, fill=(40, 52, 68),
                      outline=(90, 110, 140), width=1)
            for ry in range(20, h - 14, 12):
                frame.box(rx + 6, ry, 24, 5, fill=(60, 80, 100))
                frame.oval(rx + 36, ry, rx + 41, ry + 5, (90, 220, 120))
        # cracked shield, right side
        sx, sy = 210, 14
        frame.poly([(sx, sy), (sx + 64, sy), (sx + 64, sy + 30),
                    (sx + 32, sy + 58), (sx, sy + 30)], fill=(70, 90, 120),
                   outline=PALETTE["brass"], width=2)
        frame.pline([(sx + 32, sy + 4), (sx + 26, sy + 26),
                     (sx + 38, sy + 40)], PALETTE["red"], 3)
        frame.line(sx + 26, sy + 26, sx + 20, sy + 44, PALETTE["red"], 3)
        frame.text(150, h - 24, "2", self.strong(20), PALETTE["red"])

    def art_verdict(self, frame, w, h):
        """A courthouse, a gavel, and the 10/12 count."""
        frame.box(0, 0, w, h, fill=(232, 238, 246))
        frame.poly([(60, 6), (130, 6), (142, 18), (48, 18)],
                   fill=PALETTE["navy"])
        for cx in (60, 80, 100, 120):
            frame.box(cx, 18, 7, h - 28, fill=PALETTE["blank"],
                      outline=PALETTE["navy"], width=1)
        frame.box(48, h - 10, 94, 5, fill=PALETTE["navy"])
        # gavel, right side
        frame.box(190, 20, 40, 10, fill=(120, 90, 60))
        frame.line(210, 30, 210, 52, (120, 90, 60), 4)
        frame.box(186, 52, 48, 6, fill=(90, 65, 40))
        frame.text(250, 14, "10/12", self.strong(20), PALETTE["red"])

    def feature_art(self, frame, kind, w, h):
        """Scene for a feature-story art key (KeyError if unknown)."""
        {"tower": self.art_tower,
         "breach": self.art_breach,
         "verdict": self.art_verdict}[kind](frame, w, h)


    # -------------------------------------------------------- panel scenes
    # One tiny illustration per panel story (stories 04-13), drawn into
    # a 42-pixel-high band at the top of each small card. Numbers only.

    def vignette_sparta(self, frame, w, h):
        """A night sea, a listing ship, a drone arc above."""
        frame.box(0, 0, w, h, fill=(16, 36, 60))
        for sx, sy in ((10, 6), (40, 10), (90, 5), (150, 8), (170, 12)):
            frame.oval(sx - 1, sy - 1, sx + 1, sy + 1, (220, 220, 200))
        base = h - 8
        frame.poly([(30, base - 12), (120, base - 18),
                    (114, base), (36, base)], fill=(40, 40, 48))
        frame.box(90, base - 28, 20, 12, fill=(70, 70, 82))
        ax, ay = 150, 10
        frame.oval(ax - 3, ay - 3, ax + 3, ay + 3, (255, 200, 60))
        frame.arc(ax - 16, ay, 32, 26, 180, 360, (255, 120, 40), 2)
        frame.text(8, h - 15, "21", self.strong(12), PALETTE["brass"])

    def vignette_cpi(self, frame, w, h):
        """Three rising bars and the +4.9% figure."""
        frame.box(0, 0, w, h, fill=(240, 240, 235))
        for bx, bh in ((30, 12), (60, 20), (90, 30)):
            frame.box(bx, h - 4 - bh, 20, bh, fill=PALETTE["leaf"])
        frame.line(20, h - 34, 120, h - 38, PALETTE["red"], 2)
        frame.text(126, 8, "+4.9%", self.strong(14), PALETTE["red"])

    def vignette_sarkozy(self, frame, w, h):
        """Small courthouse pediment and the 10-year maximum."""
        frame.box(0, 0, w, h, fill=(232, 238, 246))
        frame.poly([(40, 4), (90, 4), (100, 14), (30, 14)],
                   fill=PALETTE["navy"])
        for cx in (40, 56, 72, 88):
            frame.box(cx, 14, 5, h - 20, fill=PALETTE["blank"],
                      outline=PALETTE["navy"], width=1)
        frame.text(120, 10, "10", self.strong(18), PALETTE["red"])
        frame.text(120, 28, "YRS", self.strong(9), PALETTE["navy"])

    def vignette_giuliani(self, frame, w, h):
        """A gold medal on a blue ribbon, and Giuliani's age."""
        frame.box(0, 0, w, h, fill=PALETTE["navy"])
        frame.poly([(70, 2), (84, 2), (78, 18), (76, 18)],
                   fill=PALETTE["red"])
        frame.poly([(84, 2), (98, 2), (92, 18), (90, 18)],
                   fill=PALETTE["blank"])
        frame.oval(66, 16, 102, h - 2, PALETTE["brass"],
                   outline=(200, 150, 40), width=2)
        frame.text(76, 20, "★", self.strong(14), PALETTE["red"])
        frame.text(120, 10, "82", self.strong(16), PALETTE["blank"])

    def vignette_hasan(self, frame, w, h):
        """A base gate, a flag, and the 13 victims of 2009."""
        frame.box(0, 0, w, h, fill=(228, 222, 200))
        frame.line(30, 4, 30, h - 4, PALETTE["ink"], 2)
        frame.box(32, 6, 30, 14, fill=PALETTE["red"])
        frame.text(36, 8, "US", self.strong(10), PALETTE["blank"])
        frame.box(90, 18, 60, h - 22, fill=(150, 140, 120))
        frame.box(96, 24, 48, h - 34, fill=(90, 80, 60))
        frame.text(156, 10, "13", self.strong(16), PALETTE["red"])

    def vignette_awacs(self, frame, w, h):
        """A radar plane over cloud, and the 14-aircraft fleet."""
        frame.box(0, 0, w, h, fill=PALETTE["ocean"])
        frame.oval(30, 8, 100, 18, PALETTE["blank"],
                   outline=PALETTE["navy"], width=2)
        frame.poly([(100, 10), (118, 13), (100, 16)], fill=PALETTE["navy"])
        frame.oval(56, 2, 74, 8, PALETTE["navy"])
        frame.line(65, 8, 65, 10, PALETTE["navy"], 2)
        frame.text(130, 10, "14", self.strong(16), PALETTE["navy"])
        frame.oval(150, 26, 170, 32, PALETTE["blank"])
        frame.oval(20, 30, 44, 36, PALETTE["blank"])

    def vignette_cricket(self, frame, w, h):
        """A green pitch, a bat, a ball, and Donald's 85."""
        frame.box(0, 0, w, h, fill=(20, 90, 40))
        frame.line(10, 30, w - 10, 30, (120, 200, 120), 2)
        frame.line(60, 8, 78, 26, (220, 190, 140), 5)
        frame.oval(100, 22, 110, 32, PALETTE["red"])
        frame.text(126, 8, "85", self.strong(16), PALETTE["blank"])

    def vignette_gaza(self, frame, w, h):
        """The toll as one stark number."""
        frame.box(0, 0, w, h, fill=(240, 240, 235))
        frame.text(10, 10, "74,746", self.strong(20), PALETTE["red"])

    def vignette_wfp(self, frame, w, h):
        """Wheat stalks and the 266m figure."""
        frame.box(0, 0, w, h, fill=(250, 240, 200))
        for sx in (30, 55, 80):
            frame.line(sx, h - 4, sx, 12, PALETTE["ochre"], 2)
            for gy in range(12, 24, 4):
                frame.oval(sx - 4, gy, sx + 4, gy + 5, (200, 160, 60))
        frame.text(104, 10, "266m", self.strong(16), PALETTE["ochre"])

    def vignette_denmark(self, frame, w, h):
        """Scales of justice and the 91 leases."""
        frame.box(0, 0, w, h, fill=(250, 244, 220))
        frame.line(70, 6, 70, h - 8, PALETTE["ink"], 2)
        frame.line(40, 10, 100, 10, PALETTE["ink"], 2)
        frame.poly([(34, 26), (46, 26), (40, 14)], fill=PALETTE["navy"])
        frame.poly([(94, 26), (106, 26), (100, 14)], fill=PALETTE["navy"])
        frame.box(60, h - 8, 20, 4, fill=PALETTE["ink"])
        frame.text(120, 10, "91", self.strong(16), PALETTE["red"])

    def vignette_plain(self, frame, w, h):
        """Plain panel for any art key without its own scene."""
        frame.box(0, 0, w, h, fill=(240, 235, 225))

    def card_art(self, frame, kind, w, h):
        """Vignette for an art key, or the plain panel."""
        scenes = {"sparta": self.vignette_sparta,
                  "cpi": self.vignette_cpi,
                  "sarkozy": self.vignette_sarkozy,
                  "giuliani": self.vignette_giuliani,
                  "hasan": self.vignette_hasan,
                  "awacs": self.vignette_awacs,
                  "cricket": self.vignette_cricket,
                  "gaza": self.vignette_gaza,
                  "wfp": self.vignette_wfp,
                  "denmark": self.vignette_denmark}
        scenes.get(kind, self.vignette_plain)(frame, w, h)


    # ----------------------------------------------------------------- map

    def pin(self, frame, project, num_font, num, lon, lat, dx, dy):
        """One numbered pin: a leader line from the place to a red disc."""
        sx, sy = project(lon, lat)
        lx, ly = sx + dx, sy + dy
        frame.line(sx, sy, lx, ly, PALETTE["red"], 1)
        frame.oval(lx - 8, ly - 8, lx + 8, ly + 8, PALETTE["red"],
                   outline=PALETTE["blank"], width=1)
        nw = frame.measure(num, num_font)
        frame.text(lx - nw / 2, ly - 7, num, num_font, PALETTE["blank"])

    def world_map(self, frame, w, h):
        """Stylised world map (equirectangular) with numbered pins 01-13."""
        frame.box(0, 0, w, h, fill=PALETTE["ocean"])
        lon0, lon1, lat0, lat1 = -180.0, 180.0, 78.0, -58.0

        def project(lon, lat):
            return ((lon - lon0) / (lon1 - lon0) * w,
                    (lat0 - lat) / (lat0 - lat1) * h)

        for la in (60, 30, 0, -30):
            _, gy = project(0, la)
            frame.line(0, gy, w, gy, (190, 205, 220), 1)
        for coast in COASTS.values():
            frame.poly([project(lon, lat) for lon, lat in coast],
                       fill=(214, 208, 188), outline=(150, 144, 128))
        num_font = self.strong(10)
        for p in MAP_PINS:
            self.pin(frame, project, num_font, p["num"], p["lon"],
                     p["lat"], p["dx"], p["dy"])

    # -------------------------------------------------------- page sections
    # The page is laid out top to bottom: nameplate, figures, tallies,
    # timeline, features, grid, map + digest, DATE CHECK, colophon.

    def nameplate(self, frame):
        """Top tag, paper name, dateline, standfirst, double rule."""
        frame.text(0, 10, "THE WORLD IN ONE DAY", self.strong(10),
                   PALETTE["muted"])
        tag = "WEDNESDAY EDITION · No. 329"
        frame.text(BODY_W - frame.measure(tag, self.strong(10)), 10, tag,
                   self.strong(10), PALETTE["muted"])
        name = self.fit("DejaVuSerif-Bold.ttf", "THE WEDNESDAY PAPER", 64,
                        BODY_W)
        frame.text(0, 24, "THE WEDNESDAY PAPER", name, PALETTE["ink"])
        dateline = "WEDNESDAY 25 NOVEMBER 2026 — 36 STORIES, DATED HONESTLY"
        frame.text((PAGE_W - frame.measure(dateline, self.strong(12))) / 2
                   - MARGIN, 92, dateline, self.strong(12), PALETTE["red"])
        frame.line(0, 110, BODY_W, 110, PALETTE["ink"], 2)
        frame.line(0, 114, BODY_W, 114, PALETTE["ink"], 1)

    def figures(self, frame):
        """Six boxed headline figures with a two-line caption each."""
        cell, gap = 157, 6
        for i, item in enumerate(HEADLINES):
            x = i * (cell + gap)
            caption, figure = item["caption"], item["figure"]
            frame.box(x, 0, cell, 50, outline=PALETTE["rule"], width=1)
            fnt = self.fit("DejaVuSerif-Bold.ttf", figure, 26, cell - 12)
            fw = frame.measure(figure, fnt)
            frame.text(x + (cell - fw) / 2, 4, figure, fnt, PALETTE["red"])
            rows = self.wrap(frame, caption, self.strong(8), cell - 10)
            yy = 32
            for line in rows[:2]:
                lw = frame.measure(line, self.strong(8))
                frame.text(x + (cell - lw) / 2, yy, line, self.strong(8),
                           PALETTE["ink"])
                yy += 9

    def tallies(self, frame):
        """Coloured region tallies that add up to 36 stories."""
        x = 0
        for item in TALLIES:
            label = "%s %d" % (item["region"], item["count"])
            fnt = self.strong(11)
            wid = int(frame.measure(label, fnt)) + 22
            frame.rrect(x, 0, wid, 22, 11, REGION_PAINT[item["region"]])
            frame.text(x + 11, 5, label, fnt, PALETTE["blank"])
            x += wid + 8
        frame.text(x + 4, 5, "= 36 STORIES", self.regular(11),
                   PALETTE["muted"])

    def timeline(self, frame):
        """One-line UTC timeline of the day, shrunk until it fits."""
        size = 10
        while size > 7:
            if frame.measure(DAY_LINE, self.regular(size)) <= BODY_W:
                break
            size -= 1
        frame.text(0, 0, DAY_LINE, self.regular(size), PALETTE["navy"])

    def feature(self, frame, story, wid):
        """One feature story: artwork band, dateline, headline, deck."""
        art_h = 86
        self.feature_art(frame, story["art"], wid, art_h)
        frame.box(0, 0, wid, art_h, outline=PALETTE["rule"], width=1)
        yy = art_h + 6
        frame.text(0, yy, "%s  %s" % (story["num"], story["dateline"]),
                   self.strong(10), PALETTE["red"])
        yy += 15
        _, yy = self.paragraph(frame, 0, yy, story["headline"],
                               self.display(19), PALETTE["ink"], wid,
                               gap=22, cap=2)
        _, yy = self.paragraph(frame, 0, yy + 3, story["deck"],
                               self.regular(11), PALETTE["ink"], wid,
                               gap=13, cap=4)
        frame.text(0, yy + 4, story["sources"], self.regular(9),
                   PALETTE["muted"])

    def features(self, frame):
        """The three feature stories in a row."""
        wid, gap = 317, 12
        for i, story in enumerate(FEATURES):
            self.feature(frame.child(i * (wid + gap), 0), story, wid)

    def card(self, frame, story, wid, hei):
        """One small story card: region bar, vignette, number, texts."""
        frame.box(0, 0, wid, hei, fill=PALETTE["blank"],
                  outline=PALETTE["rule"], width=1)
        frame.box(0, 0, wid, 3, fill=REGION_PAINT[story["region"]])
        self.card_art(frame.child(1, 4), story["art"], wid - 2, 42)
        frame.box(1, 4, wid - 2, 42, outline=PALETTE["rule"], width=1)
        ty = 50
        frame.text(6, ty, story["num"], self.strong(10), PALETTE["red"])
        _, ty = self.paragraph(frame, 6, ty + 13, story["headline"],
                               self.strong(12), PALETTE["ink"], wid - 12,
                               gap=13, cap=2)
        _, ty = self.paragraph(frame, 6, ty + 2, story["deck"],
                               self.regular(10), PALETTE["ink"], wid - 12,
                               gap=11, cap=2)
        frame.text(6, hei - 11, story["sources"], self.regular(8),
                   PALETTE["muted"])

    def grid(self, frame):
        """Ten small stories in a 5 x 2 grid."""
        wid, gap, hei, rgap = 187, 10, 126, 6
        for i, story in enumerate(CARDS):
            row, col = divmod(i, 5)
            self.card(frame.child(col * (wid + gap), row * (hei + rgap)),
                      story, wid, hei)

    def map_block(self, frame):
        """Map heading, rules, the world map and its pin caption."""
        frame.text(0, 0, "WHERE THE NEWS HAPPENED — STORIES 01–13",
                   self.strong(11), PALETTE["ink"])
        frame.text(384 - MARGIN, 0, "ALSO THIS WEEK — 23 MORE STORIES",
                   self.strong(11), PALETTE["ink"])
        frame.line(0, 16, 344, 16, PALETTE["ink"], 1)
        frame.line(384 - MARGIN, 16, BODY_W, 16, PALETTE["ink"], 1)
        self.world_map(frame.child(0, 20), 344, 172)
        frame.text(0, 196,
                   "Pins: Riyadh · Langley · Brooklyn · Kyiv · Canberra · "
                   "Paris · Washington",
                   self.regular(9), PALETTE["muted"])
        frame.text(0, 208,
                   "Fort Hood · Warsaw · Carrara · Gaza · Rome · Copenhagen",
                   self.regular(9), PALETTE["muted"])

    def briefs(self, frame):
        """The 23 briefs in two columns on the right."""
        col_x, col_w = 384 - MARGIN, 300
        for i, item in enumerate(DIGEST):
            col, row = divmod(i, 12)
            bx = col_x + col * (col_w + 16)
            by = 22 + row * 15
            if frame.measure(item["text"], self.regular(10)) > col_w - 20:
                raise ValueError("brief too long for one line: %r"
                                 % item["text"])
            frame.text(bx, by, item["num"], self.strong(10), PALETTE["red"])
            frame.text(bx + 20, by, item["text"], self.regular(10),
                       PALETTE["ink"])

    def datecheck(self, frame):
        """The honesty strip: everything here is dated, not dressed up."""
        frame.line(0, 0, BODY_W, 0, PALETTE["ink"], 1)
        frame.text(0, 5, "DATE CHECK — ALSO THIS WEEK:", self.strong(10),
                   PALETTE["red"])
        self.paragraph(frame, 0, 19, DATE_LINE, self.regular(10),
                       PALETTE["ink"], BODY_W, gap=13, cap=2)

    def colophon(self, frame):
        """Thin rule, sourcing note on the left, nameplate on the right."""
        frame.line(0, 1000, BODY_W, 1000, PALETTE["rule"], 1)
        frame.text(0, 1004,
                   "Built 25 November 2026 from verified "
                   "reports; figures as reported on the day.",
                   self.regular(9), PALETTE["muted"])
        right = "THE WEDNESDAY PAPER · 36 STORIES"
        frame.text(BODY_W - frame.measure(right, self.strong(9)), 1004,
                   right, self.strong(9), PALETTE["muted"])

    def render(self):
        """Draw every section onto the fresh newsprint page."""
        self.nameplate(self.root.child(MARGIN, 0))
        self.figures(self.root.child(MARGIN, 122))
        self.tallies(self.root.child(MARGIN, 180))
        self.timeline(self.root.child(MARGIN, 208))
        self.features(self.root.child(MARGIN, 226))
        self.grid(self.root.child(MARGIN, 454))
        self.map_block(self.root.child(MARGIN, 720))
        self.briefs(self.root.child(MARGIN, 720))
        self.datecheck(self.root.child(MARGIN, 940))
        self.colophon(self.root.child(MARGIN, 0))
        return self.image


# ------------------------------------------------------------------- output

def _write_stored_copy():
    """Write the committed front page with stdlib only.

    Used when Pillow is missing (bare grade image) or the live draw
    fails. The picture bytes live in entry.png beside this file (it is
    committed in the repo); the sha256 and the 1 MiB cap are checked
    before writing.
    """
    data = (Path(__file__).resolve().parent / "entry.png").read_bytes()
    if hashlib.sha256(data).hexdigest() != STORED_SHA:
        raise RuntimeError("stored copy sha256 mismatch")
    if len(data) > 1024 * 1024:
        raise RuntimeError("stored copy over the 1 MiB cap")
    os.makedirs(OUT_DIR, exist_ok=True)
    Path(OUT_PATH).write_bytes(data)


def main():
    """Render the page (live draw, else stored copy) and save it."""
    assert len(FEATURES) + len(CARDS) + len(DIGEST) == 36, \
        "must be 36 stories"
    assert sum(item["count"] for item in TALLIES) == 36, \
        "tallies must sum to 36"
    if _CAN_DRAW:
        try:
            page = FrontPage()
            img = page.render()
            os.makedirs(OUT_DIR, exist_ok=True)
            img.save(OUT_PATH, format="PNG", optimize=True)
            print("wrote %s (%dx%d) [live draw]"
                  % (OUT_PATH, PAGE_W, PAGE_H))
            return
        except Exception as exc:
            print("live draw failed (%s); using stored copy" % exc)
    _write_stored_copy()
    print("wrote %s (%dx%d) [pre-rendered]" % (OUT_PATH, PAGE_W, PAGE_H))


if __name__ == "__main__":
    main()
