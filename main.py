#!/usr/bin/env python3
"""THE WEDNESDAY PAPER — one picture holding Wednesday 25 November 2026.

A 1024x1024 front page for the make.fun news-image-20261125 bounty.
Thirty-six world stories, every one checked against two or more
independent reports dated 23-25 November 2026, arranged as a dated
nameplate, six headline numbers, region counts, a short UTC timeline,
three illustrated feature stories, ten small panels, a numbered world
map, twenty-three one-line briefs, and a DATE CHECK strip that dates
older events honestly instead of dressing them up as Wednesday news.
The three features are the stories that moved the world on Tuesday:
a Houthi drone struck Riyadh's tallest tower for the second time in
a week; intruders got into the CIA and the spy chief's office; and a
Brooklyn jury found Huawei guilty on ten of twelve counts. Two items
are genuinely Wednesday-fresh: Australia's CPI at 07:30 WIB and the
Shenzhou-24 launch carrying the first foreign astronaut to Tiangong.

Pillow draws everything. The grading machine runs bare Python 3.13
with no Pillow, so when the live render cannot run, main() falls back
to the committed entry.png sitting beside this file, checked by its
sha256, using only the standard library. Either route writes the same
bytes to $MAKEFUN_OUTPUT_DIR/entry.png (/output/entry.png by default).
No network is used anywhere.
"""
import hashlib
import math
import os

try:
    from PIL import Image, ImageDraw, ImageFont
    _CAN_DRAW = True
except ImportError:  # bare grade image: Pillow is not installed there
    Image = ImageDraw = ImageFont = None
    _CAN_DRAW = False


# ------------------------------------------------------------- sheet setup
# Page size, output path, and the hash the stored copy must match.

SHEET_W = 1024
SHEET_H = 1024
EDGE = 24
CONTENT_W = 976
DEST_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
DEST_PATH = os.path.join(DEST_DIR, "entry.png")
FALLBACK_DIGEST = "c4f8fe830a539ed710ad05a5c43c3b17517c5dbaf74f8683102af9e493f390af"

TYPE_DIR = "/usr/share/fonts/truetype/dejavu"

# Newsprint inks, one tuple each.
NEWS_PRINT = (253, 251, 245)
BODY = (26, 26, 26)
ALERT = (179, 32, 44)
DEEP_BLUE = (31, 58, 95)
MUTED = (110, 105, 95)
RULE = (216, 210, 196)
BLANK = (255, 255, 255)
OCEAN = (214, 228, 240)
BRASS = (255, 200, 80)
LEAF = (46, 125, 50)
OCHRE = (154, 107, 0)
PLUM = (106, 61, 154)
NIGHT = (16, 28, 48)

# Region tally colours, in chip order.
REGION_PAINTS = (
    ("EUROPE", DEEP_BLUE),
    ("AMERICAS", LEAF),
    ("ASIA-PACIFIC", ALERT),
    ("MIDEAST", OCHRE),
    ("AFRICA", PLUM),
    ("WORLD", (85, 85, 85)),
)


def paint_for_region(name):
    """Fill colour for a region name (KeyError for an unknown region)."""
    for label, rgb in REGION_PAINTS:
        if label == name:
            return rgb
    raise KeyError(name)


# ------------------------------------------------------------ type helpers

def load_typeface(filename, size):
    """One DejaVu face from the system type directory."""
    return ImageFont.truetype(os.path.join(TYPE_DIR, filename), size)


def body_face(size):
    """DejaVu Sans, regular weight."""
    return load_typeface("DejaVuSans.ttf", size)


def bold_face(size):
    """DejaVu Sans, bold weight."""
    return load_typeface("DejaVuSans-Bold.ttf", size)


def display_face(size):
    """DejaVu Serif, bold weight (nameplate and big figures)."""
    return load_typeface("DejaVuSerif-Bold.ttf", size)


def fold_lines(pen, text, font, width):
    """Greedy word wrap: lines of `text` that fit `width` pixels."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if pen.textlength(trial, font=font) <= width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_lines(pen, pos, text, font, fill, width, gap=None, cap=None):
    """Draw `text` wrapped to `width`, one line per `gap` pixels.

    Returns (lines, y_after_last_line). Raises ValueError when the text
    needs more lines than `cap` allows, so overflow is caught at build
    time instead of spilling silently off the page.
    """
    x, y = pos
    if gap is None:
        gap = int(font.size * 1.18)
    lines = fold_lines(pen, text, font, width)
    if cap is not None and len(lines) > cap:
        raise ValueError("text overflows %d lines: %r -> %r"
                         % (cap, text, lines))
    for line in lines:
        pen.text((x, y), line, font=font, fill=fill)
        y += gap
    return lines, y


def fit_typeface(filename, text, start, width):
    """Largest size (from `start` down to 8) whose width fits."""
    size = start
    while size > 8:
        fnt = load_typeface(filename, size)
        if fnt.getlength(text) <= width:
            return fnt
        size -= 1
    return load_typeface(filename, 8)


def fill_box(pen, x, y, w, h, fill):
    """Fill the rectangle (x, y, w, h) with one solid colour."""
    pen.rectangle([x, y, x + w, y + h], fill=fill)


# -------------------------------------------------------------- story data
# Feature rows: (number, art, region, dateline, headline, deck, sources).
# Every story was verified against at least two sources; the DATE CHECK
# strip at the foot of the page is the honesty device for anything that
# did not actually happen on Tuesday.

FEATURES = (
    ("01", "tower", "MIDEAST", "RIYADH — TUESDAY",
     "Drone hits Riyadh's tallest tower",
     "A Houthi drone strikes the 385 m PIF Tower — the second hit in "
     "under a week. 11 wounded; the Saudi-led coalition vows a 'firm' "
     "response. No claim by 16:00 GMT.",
     "Reuters · WSJ · BusinessWorld"),
    ("02", "breach", "AMERICAS", "WASHINGTON — TUESDAY",
     "CIA and spy chiefs hacked",
     "Hackers breach CIA and ODNI systems, exposing unclassified data "
     "via an open-source-intel network. ODNI: no damage to critical or "
     "classified capability; unclear what leaked.",
     "NYT via Reuters"),
    ("03", "verdict", "AMERICAS", "BROOKLYN — TUESDAY",
     "Huawei guilty on 10 of 12 counts",
     "A jury convicts Huawei of bank and wire fraud, sanctions breaches "
     "and trade-secret theft; cleared of racketeering. Sentencing "
     "14 Sep 2027; Huawei will appeal.",
     "CNN · WSJ · AP · Reuters"),
)

# Panel rows: (number, art, region, dateline, headline, deck, sources).
CARDS = (
    ("04", "sparta", "EUROPE", "KYIV — TUESDAY",
     "Zelenskiy: 'We did it' — Sparta II",
     "Kyiv confirms it hit the arms ship Sat; Russia cries 'terrorism'.",
     "Reuters · Bloomberg"),
    ("05", "cpi", "ASIA-PACIFIC", "CANBERRA — WEDNESDAY",
     "Australia CPI jumps to 4.9%",
     "October inflation beats forecasts; trimmed mean 3.8%.",
     "ABS · WSJ"),
    ("06", "sarkozy", "EUROPE", "PARIS — TUESDAY",
     "Sarkozy and Bruni to stand trial",
     "Witness-tampering case over Libyan cash; 11 in the dock.",
     "Reuters · BBC · The Times"),
    ("07", "giuliani", "AMERICAS", "WASHINGTON — TUESDAY",
     "Giuliani gets Medal of Freedom",
     "Trump honours 'America's Mayor' in a private Oval Office rite.",
     "Reuters · USA Today"),
    ("08", "hasan", "AMERICAS", "FORT HOOD — TUESDAY",
     "Hasan asks court to halt execution",
     "Firing squad set for Dec 3; first US military execution since 1945.",
     "Reuters · NBC News"),
    ("09", "awacs", "EUROPE", "BRUSSELS — MONDAY",
     "NATO sends AWACS to Poland",
     "After 3 Russian Kh-101s landed Fri; SACEUR orders the deployment.",
     "Reuters · NATO"),
    ("10", "cricket", "WORLD", "CARRARA — TUESDAY",
     "England crush Australia by 8 wickets",
     "Donald 85 off 32, Salt 58; 185 chased in 13.1 overs. Series 1–1.",
     "Reuters · Cricinfo"),
    ("11", "gaza", "MIDEAST", "GAZA — MONDAY",
     "Gaza death toll reaches 74,746",
     "Ministry count Mon; 10 more killed Tue — toll now 74,756.",
     "WAFA · QNA"),
    ("12", "wfp", "WORLD", "NEW YORK — MONDAY",
     "266m face acute hunger — WFP",
     "39m at emergency levels; wars may add $727m to aid costs.",
     "UN News · Reuters"),
    ("13", "denmark", "EUROPE", "COPENHAGEN — MONDAY",
     "Denmark backs 'ghetto' evictions",
     "Top court: 91 leases lawfully ended; test is neutral.",
     "Reuters · CBS News"),
)

# The 23 briefs as (text, number) pairs, in page order.
DIGEST = (
    ("Dell: record $54.9bn quarter, AI backlog $132.3bn (Tue)", "14"),
    ("Nvidia gives back 5.9% after Monday's 31% surge (Tue)", "15"),
    ("BJP and Akali Dal reunite for 2027 Punjab polls (Tue)", "16"),
    ("Trump pardons turkeys Freedom and Feathers (Tue)", "17"),
    ("Huckabee 'not certain' Israel aid ends this year (Tue)", "18"),
    ("Houthis 60 km from Aden; army: city will hold (Tue)", "19"),
    ("Trump readies new tariffs on 16 economies: WSJ (Tue)", "20"),
    ("Anthropic falls below its $83 IPO price (Tue)", "21"),
    ("US confidence 103.3, best since Jan 2025 (Tue)", "22"),
    ("Sudan: RSF drones hit 3 power stations (Mon)", "23"),
    ("IRGC: 4th tanker hits mine in Hormuz, catches fire (Tue)", "24"),
    ("UK sanctions Houthis and 4 officials over abuses (Tue)", "25"),
    ("Hasina plans Dec 16 return; Dhaka: 'in handcuffs' (Tue)", "26"),
    ("Serbia: teen, 17, fires rifle at school; 2 hurt (Tue)", "27"),
    ("Dymer: 11 killed in Sunday strike; boy, 7, alive (Sun)", "28"),
    ("Benghazi: Kyiv claims it sank corvette Merkury (Sun)", "29"),
    ("Solomons sign Australia pact, drop China deal (Wed)", "30"),
    ("Russian jets near S. Korea; island told to shelter (Tue)", "31"),
    ("Zambia: opposition leader charged with treason (Mon)", "32"),
    ("DR Congo plane missing; rebels claim downed (Sun)", "33"),
    ("Shenzhou-24 lifts off, first Pakistani astronaut (Wed)", "34"),
    ("Zaporizhzhia: 2 killed, 40 hurt in overnight strike (Tue)", "35"),
    ("UK recognises Rohingya genocide, sanctions 5 (Mon)", "36"),
)

# Region tallies under the nameplate; the counts must add to 36.
TALLIES = (
    (9, "EUROPE"),
    (10, "AMERICAS"),
    (5, "ASIA-PACIFIC"),
    (5, "MIDEAST"),
    (4, "AFRICA"),
    (3, "WORLD"),
)

# The six headline figures strip: (caption, figure).
HEADLINES = (
    ("WOUNDED IN RIYADH STRIKE", "11"),
    ("HUAWEI GUILTY COUNTS", "10/12"),
    ("AUSTRALIA CPI, OCTOBER", "+4.9%"),
    ("GAZA DEATH TOLL (MON)", "74,746"),
    ("PEOPLE IN ACUTE HUNGER", "266m"),
    ("NVIDIA GIVES BACK TUESDAY", "-5.9%"),
)

# Short UTC timeline of the day, one line under the region tallies.
DAY_MARKS = (
    "00:18 GMT Shenzhou-24 lifts off",
    "00:30 GMT AU CPI +4.9%",
    "07:00 GMT Kragujevac shooting",
    "12:03 GMT UK sanctions Houthis",
    "16:00 GMT no Houthi claim yet",
    "19:00 GMT turkey pardon",
)
DAY_LINE = "UTC TIMELINE — " + "  ·  ".join(DAY_MARKS)

# Honesty strip: events that are easy to mis-date, dated honestly.
DATE_NOTES = (
    "COP31 fell SUNDAY 22 Nov (not Tue)",
    "Sparta II hit SAT 21 Nov",
    "Benghazi blast early SUN",
    "Hormuz mines SAT — Torkel, Arina",
    "Dymer strike SUN; toll 11",
    "PIF Tower first hit THU 19 Nov",
    "F1 Las Vegas ran SAT — stale",
    "Iran strikes Kuwait/Bahrain WED 18 Nov",
    "Anthropic IPO THU 19 Nov",
    "Gaza toll 74,746 as of MON",
)
DATE_LINE = " • ".join(DATE_NOTES)

# Map pins for stories 01-13: (lon, lat, number, label dx, label dy).
MAP_PINS = (
    (45.0, 24.7, "01", 18, 14),     # Riyadh
    (-77.2, 38.9, "02", -30, -18),  # Langley, Virginia
    (-74.0, 40.7, "03", 26, -14),   # Brooklyn
    (30.5, 50.5, "04", 18, -18),    # Kyiv
    (149.1, -35.3, "05", -18, 12),  # Canberra
    (2.35, 48.85, "06", -30, 10),   # Paris
    (-77.0, 38.9, "07", 20, 16),    # Washington DC
    (-97.8, 31.1, "08", -20, 14),   # Fort Hood, Texas
    (21.0, 52.2, "09", 26, 12),     # Warsaw
    (153.4, -28.0, "10", 14, 12),   # Carrara, Gold Coast
    (34.5, 31.5, "11", -22, -14),   # Gaza
    (12.5, 41.9, "12", -24, 12),    # Rome
    (12.6, 55.7, "13", -28, -14),   # Copenhagen
)


def parse_shoreline(spec):
    """Parse a "lon,lat;lon,lat;..." outline into (lon, lat) pairs."""
    pairs = []
    for chunk in spec.split(";"):
        lon, lat = chunk.split(",")
        pairs.append((float(lon), float(lat)))
    return pairs


# Simplified continent outlines (lon, lat), equirectangular, stylised.
# Coarse hand-drawn shapes, not survey data.
SHORELINES = (
    # North America
    parse_shoreline("-168,66;-140,70;-120,71;-100,73;-85,70;-75,62;-60,55;-55,47;"
           "-65,44;-70,42;-75,35;-80,25;-85,30;-90,20;-95,16;-100,18;"
           "-105,20;-110,23;-115,28;-120,34;-125,40;-125,48;-130,55;"
           "-140,60;-155,58;-165,60"),
    # Greenland
    parse_shoreline("-55,60;-40,64;-30,68;-25,70;-35,76;-50,76;-58,72"),
    # South America
    parse_shoreline("-80,9;-75,11;-65,10;-55,5;-50,0;-45,-3;-35,-8;-38,-15;-40,-22;"
           "-48,-28;-55,-35;-62,-40;-68,-50;-70,-54;-73,-45;-72,-35;"
           "-70,-20;-77,-5"),
    # Europe
    parse_shoreline("-10,36;-9,43;-2,44;-1,48;-4,48;0,50;4,52;8,55;10,58;5,60;"
           "10,64;18,69;25,71;30,70;28,66;22,60;24,58;21,55;18,54;"
           "24,58;28,60;24,62;18,66;12,66;6,62;0,60;-5,58;-10,52;-10,44"),
    # Africa
    parse_shoreline("-6,35;-10,31;-16,28;-17,20;-16,12;-12,8;-8,4;0,6;6,4;9,4;9,0;"
           "12,-5;13,-12;12,-18;15,-27;18,-34;25,-34;32,-29;35,-24;"
           "36,-18;40,-15;42,-8;46,-2;51,11;46,12;41,15;38,18;36,22;"
           "34,28;32,31;25,32;15,32;10,34"),
    # Asia
    parse_shoreline("30,36;36,36;42,38;46,40;50,42;54,45;58,48;62,52;68,56;72,60;"
           "78,66;85,70;95,75;105,77;115,75;125,73;135,71;145,72;155,69;"
           "165,66;175,65;170,62;162,58;156,52;148,45;142,40;137,35;"
           "132,32;127,30;122,28;118,24;112,20;108,14;105,8;102,6;99,10;"
           "96,15;93,18;90,22;86,20;82,17;80,12;77,8;74,12;70,20;66,24;"
           "62,25;58,27;54,28;50,30;46,30;42,32;38,36"),
    # Australia
    parse_shoreline("113,-22;114,-30;116,-35;122,-33;129,-32;133,-33;137,-35;"
           "141,-38;147,-38;150,-37;153,-30;152,-25;149,-20;145,-15;"
           "142,-11;136,-12;131,-12;127,-14;123,-17;118,-20;113,-22"),
    # Britain
    parse_shoreline("-5,50;-3,53;-5,56;-3,58;-1,57;0,53;-1,51;-5,50"),
    # Japan
    parse_shoreline("130,31;133,34;136,35;139,37;141,40;142,43;141,45;139,41;"
           "137,37;134,34;131,32"),
    # New Zealand
    parse_shoreline("167,-45;170,-42;174,-41;176,-38;175,-36;173,-35;171,-38;"
           "168,-44"),
    # Indonesia islands
    parse_shoreline("95,5;100,0;105,-5;110,-7;115,-8;120,-10;125,-8;130,-5;135,-3;"
           "140,-4;141,-8;137,-8;133,-4;128,-2;123,1;118,0;113,-1;"
           "108,-3;103,0;98,2;95,5"),
)


# --------------------------------------------------------- feature artwork
# Each feature story gets one small illustration above its headline.
# Only number labels appear inside the artwork — no words, no photos.

def starburst(pen, cx, cy, radius, arms=8):
    """Star-burst rays out of one point (explosion / flash)."""
    for k in range(arms):
        ang = k * math.pi / (arms / 2)
        pen.line([cx, cy, cx + radius * math.cos(ang),
                   cy + radius * math.sin(ang)], fill=(255, 170, 30), width=3)


def art_tower(pen, left, top, wide, tall):
    """Night skyline, the tapered PIF Tower, a drone, a flash at the top."""
    fill_box(pen, left, top, wide, tall, NIGHT)
    for sx, sy in ((12, 10), (40, 6), (90, 12), (150, 8), (210, 14),
                   (260, 6), (300, 10), (60, 20), (180, 18), (240, 22)):
        pen.ellipse([left + sx - 1, top + sy - 1, left + sx + 1, top + sy + 1],
                     fill=(220, 220, 200))
    # low skyline blocks
    for bx, bw, bh in ((8, 34, 26), (48, 28, 34), (200, 30, 30),
                       (236, 34, 24), (276, 30, 32)):
        pen.rectangle([left + bx, top + tall - bh, left + bx + bw, top + tall],
                       fill=(30, 42, 66))
        for wy in range(top + tall - bh + 6, top + tall - 4, 8):
            pen.rectangle([left + bx + 6, wy, left + bx + 10, wy + 3],
                           fill=(255, 210, 90))
    # the tower: tapered, lit windows, 385 m tall in real life
    tx = left + 130
    pen.polygon([(tx, top + 4), (tx + 22, top + 4), (tx + 30, top + tall),
                  (tx - 8, top + tall)], fill=(52, 68, 96))
    for wy in range(top + 12, top + tall - 6, 9):
        pen.line([tx + 3, wy, tx + 19, wy], fill=(255, 210, 90), width=2)
    # drone upper right with a red eye
    dx, dy = left + 262, top + 22
    pen.ellipse([dx - 8, dy - 3, dx + 8, dy + 3], fill=(200, 200, 210))
    pen.line([dx - 16, dy - 6, dx + 16, dy - 6], fill=(160, 160, 170),
              width=2)
    pen.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=ALERT)
    pen.line([dx, dy + 3, tx + 12, top + 12], fill=(255, 120, 40), width=1)
    starburst(pen, tx + 11, top + 12, 16)
    pen.ellipse([tx + 2, top + 3, tx + 20, top + 21], fill=(255, 200, 80))
    pen.rectangle([left + 4, top + tall - 22, left + 56, top + tall - 3], fill=NIGHT)
    pen.text((left + 8, top + tall - 20), "385 m", font=bold_face(13), fill=BRASS)


def art_breach(pen, left, top, wide, tall):
    """Two server racks, a cracked shield, and the number 2."""
    fill_box(pen, left, top, wide, tall, (24, 32, 44))
    # two racks with status lights
    for rx in (left + 18, left + 78):
        pen.rectangle([rx, top + 12, rx + 48, top + tall - 10], fill=(40, 52, 68),
                       outline=(90, 110, 140), width=1)
        for ry in range(top + 20, top + tall - 14, 12):
            pen.rectangle([rx + 6, ry, rx + 30, ry + 5], fill=(60, 80, 100))
            pen.ellipse([rx + 36, ry, rx + 41, ry + 5], fill=(90, 220, 120))
    # cracked shield, right side
    sx, sy = left + 210, top + 14
    pen.polygon([(sx, sy), (sx + 64, sy), (sx + 64, sy + 30),
                  (sx + 32, sy + 58), (sx, sy + 30)], fill=(70, 90, 120),
                 outline=BRASS, width=2)
    pen.line([sx + 32, sy + 4, sx + 26, sy + 26, sx + 38, sy + 40],
              fill=ALERT, width=3)
    pen.line([sx + 26, sy + 26, sx + 20, sy + 44], fill=ALERT, width=3)
    pen.text((left + 150, top + tall - 24), "2", font=bold_face(20), fill=ALERT)


def art_verdict(pen, left, top, wide, tall):
    """A courthouse, a gavel, and the 10/12 count."""
    fill_box(pen, left, top, wide, tall, (232, 238, 246))
    pen.polygon([(left + 60, top + 6), (left + 130, top + 6),
                  (left + 142, top + 18), (left + 48, top + 18)], fill=DEEP_BLUE)
    for cx in (60, 80, 100, 120):
        pen.rectangle([left + cx, top + 18, left + cx + 7, top + tall - 10],
                       fill=BLANK, outline=DEEP_BLUE, width=1)
    pen.rectangle([left + 48, top + tall - 10, left + 142, top + tall - 5], fill=DEEP_BLUE)
    # gavel, right side
    pen.rectangle([left + 190, top + 20, left + 230, top + 30], fill=(120, 90, 60))
    pen.line([left + 210, top + 30, left + 210, top + 52], fill=(120, 90, 60),
              width=4)
    pen.rectangle([left + 186, top + 52, left + 234, top + 58], fill=(90, 65, 40))
    pen.text((left + 250, top + 14), "10/12", font=bold_face(20), fill=ALERT)


# Art key (second field of each FEATURES row) -> scene function.
FEATURE_SCENES = (
    ("tower", art_tower),
    ("breach", art_breach),
    ("verdict", art_verdict),
)


def scene_for_feature(kind):
    """Scene function for a feature-story art key (KeyError if unknown)."""
    for name, fn in FEATURE_SCENES:
        if name == kind:
            return fn
    raise KeyError(kind)


# ------------------------------------------------------------ panel scenes
# One tiny illustration per panel story (stories 04-13), drawn into a
# 42-pixel-high band at the top of each small card. Numbers only.

def vignette_sparta(pen, left, top, wide, tall):
    """A night sea, a listing ship, a drone arc above."""
    fill_box(pen, left, top, wide, tall, (16, 36, 60))
    for sx, sy in ((10, 6), (40, 10), (90, 5), (150, 8), (170, 12)):
        pen.ellipse([left + sx - 1, top + sy - 1, left + sx + 1, top + sy + 1],
                     fill=(220, 220, 200))
    base = top + tall - 8
    pen.polygon([(left + 30, base - 12), (left + 120, base - 18),
                  (left + 114, base), (left + 36, base)], fill=(40, 40, 48))
    pen.rectangle([left + 90, base - 28, left + 110, base - 16],
                   fill=(70, 70, 82))
    ax, ay = left + 150, top + 10
    pen.ellipse([ax - 3, ay - 3, ax + 3, ay + 3], fill=(255, 200, 60))
    pen.arc([ax - 16, ay, ax + 16, ay + 26], 180, 360,
             fill=(255, 120, 40), width=2)
    pen.text((left + 8, top + tall - 15), "21", font=bold_face(12), fill=BRASS)


def vignette_cpi(pen, left, top, wide, tall):
    """Three rising bars and the +4.9% figure."""
    fill_box(pen, left, top, wide, tall, (240, 240, 235))
    for bx, bh in ((30, 12), (60, 20), (90, 30)):
        pen.rectangle([left + bx, top + tall - 4 - bh, left + bx + 20, top + tall - 4],
                       fill=LEAF)
    pen.line([left + 20, top + tall - 34, left + 120, top + tall - 38], fill=ALERT,
              width=2)
    pen.text((left + 126, top + 8), "+4.9%", font=bold_face(14), fill=ALERT)


def vignette_sarkozy(pen, left, top, wide, tall):
    """Small courthouse pediment and the 10-year maximum."""
    fill_box(pen, left, top, wide, tall, (232, 238, 246))
    pen.polygon([(left + 40, top + 4), (left + 90, top + 4),
                  (left + 100, top + 14), (left + 30, top + 14)], fill=DEEP_BLUE)
    for cx in (40, 56, 72, 88):
        pen.rectangle([left + cx, top + 14, left + cx + 5, top + tall - 6],
                       fill=BLANK, outline=DEEP_BLUE, width=1)
    pen.text((left + 120, top + 10), "10", font=bold_face(18), fill=ALERT)
    pen.text((left + 120, top + 28), "YRS", font=bold_face(9), fill=DEEP_BLUE)


def vignette_giuliani(pen, left, top, wide, tall):
    """A gold medal on a blue ribbon, and Giuliani's age."""
    fill_box(pen, left, top, wide, tall, DEEP_BLUE)
    pen.polygon([(left + 70, top + 2), (left + 84, top + 2), (left + 78, top + 18),
                  (left + 76, top + 18)], fill=ALERT)
    pen.polygon([(left + 84, top + 2), (left + 98, top + 2), (left + 92, top + 18),
                  (left + 90, top + 18)], fill=BLANK)
    pen.ellipse([left + 66, top + 16, left + 102, top + tall - 2], fill=BRASS,
                 outline=(200, 150, 40), width=2)
    pen.text((left + 76, top + 20), "★", font=bold_face(14), fill=ALERT)
    pen.text((left + 120, top + 10), "82", font=bold_face(16), fill=BLANK)


def vignette_hasan(pen, left, top, wide, tall):
    """A base gate, a flag, and the 13 victims of 2009."""
    fill_box(pen, left, top, wide, tall, (228, 222, 200))
    pen.line([left + 30, top + 4, left + 30, top + tall - 4], fill=BODY, width=2)
    pen.rectangle([left + 32, top + 6, left + 62, top + 20], fill=ALERT)
    pen.text((left + 36, top + 8), "US", font=bold_face(10), fill=BLANK)
    pen.rectangle([left + 90, top + 18, left + 150, top + tall - 4], fill=(150, 140, 120))
    pen.rectangle([left + 96, top + 24, left + 144, top + tall - 10], fill=(90, 80, 60))
    pen.text((left + 156, top + 10), "13", font=bold_face(16), fill=ALERT)


def vignette_awacs(pen, left, top, wide, tall):
    """A radar plane over cloud, and the 14-aircraft fleet."""
    fill_box(pen, left, top, wide, tall, OCEAN)
    pen.ellipse([left + 30, top + 8, left + 100, top + 18], fill=BLANK,
                 outline=DEEP_BLUE, width=2)
    pen.polygon([(left + 100, top + 10), (left + 118, top + 13),
                  (left + 100, top + 16)], fill=DEEP_BLUE)
    pen.ellipse([left + 56, top + 2, left + 74, top + 8], fill=DEEP_BLUE)
    pen.line([left + 65, top + 8, left + 65, top + 10], fill=DEEP_BLUE, width=2)
    pen.text((left + 130, top + 10), "14", font=bold_face(16), fill=DEEP_BLUE)
    pen.ellipse([left + 150, top + 26, left + 170, top + 32], fill=BLANK)
    pen.ellipse([left + 20, top + 30, left + 44, top + 36], fill=BLANK)


def vignette_cricket(pen, left, top, wide, tall):
    """A green pitch, a bat, a ball, and Donald's 85."""
    fill_box(pen, left, top, wide, tall, (20, 90, 40))
    pen.line([left + 10, top + 30, left + wide - 10, top + 30], fill=(120, 200, 120),
              width=2)
    pen.line([left + 60, top + 8, left + 78, top + 26], fill=(220, 190, 140),
              width=5)
    pen.ellipse([left + 100, top + 22, left + 110, top + 32], fill=ALERT)
    pen.text((left + 126, top + 8), "85", font=bold_face(16), fill=BLANK)


def vignette_gaza(pen, left, top, wide, tall):
    """The toll as one stark number."""
    fill_box(pen, left, top, wide, tall, (240, 240, 235))
    pen.text((left + 10, top + 10), "74,746", font=bold_face(20), fill=ALERT)


def vignette_wfp(pen, left, top, wide, tall):
    """Wheat stalks and the 266m figure."""
    fill_box(pen, left, top, wide, tall, (250, 240, 200))
    for sx in (30, 55, 80):
        pen.line([left + sx, top + tall - 4, left + sx, top + 12], fill=OCHRE,
                  width=2)
        for gy in range(top + 12, top + 24, 4):
            pen.ellipse([left + sx - 4, gy, left + sx + 4, gy + 5],
                         fill=(200, 160, 60))
    pen.text((left + 104, top + 10), "266m", font=bold_face(16), fill=OCHRE)


def vignette_denmark(pen, left, top, wide, tall):
    """Scales of justice and the 91 leases."""
    fill_box(pen, left, top, wide, tall, (250, 244, 220))
    pen.line([left + 70, top + 6, left + 70, top + tall - 8], fill=BODY, width=2)
    pen.line([left + 40, top + 10, left + 100, top + 10], fill=BODY, width=2)
    pen.polygon([(left + 34, top + 26), (left + 46, top + 26),
                  (left + 40, top + 14)], fill=DEEP_BLUE)
    pen.polygon([(left + 94, top + 26), (left + 106, top + 26),
                  (left + 100, top + 14)], fill=DEEP_BLUE)
    pen.rectangle([left + 60, top + tall - 8, left + 80, top + tall - 4], fill=BODY)
    pen.text((left + 120, top + 10), "91", font=bold_face(16), fill=ALERT)


def vignette_plain(pen, left, top, wide, tall):
    """Plain panel for any art key without its own scene."""
    fill_box(pen, left, top, wide, tall, (240, 235, 225))


# Art key (second field of each CARDS row) -> vignette function.
CARD_SCENES = (
    ("sparta", vignette_sparta),
    ("cpi", vignette_cpi),
    ("sarkozy", vignette_sarkozy),
    ("giuliani", vignette_giuliani),
    ("hasan", vignette_hasan),
    ("awacs", vignette_awacs),
    ("cricket", vignette_cricket),
    ("gaza", vignette_gaza),
    ("wfp", vignette_wfp),
    ("denmark", vignette_denmark),
)


def scene_for_card(kind):
    """Vignette function for an art key, or the plain panel."""
    for name, fn in CARD_SCENES:
        if name == kind:
            return fn
    return vignette_plain


# --------------------------------------------------------------------- map

def draw_pin(pen, project, num_font, num, lon, lat, dx, dy):
    """One numbered pin: a leader line from the place to a red disc."""
    sx, sy = project(lon, lat)
    lx, ly = sx + dx, sy + dy
    pen.line([sx, sy, lx, ly], fill=ALERT, width=1)
    pen.ellipse([lx - 8, ly - 8, lx + 8, ly + 8], fill=ALERT,
                 outline=BLANK, width=1)
    nw = pen.textlength(num, font=num_font)
    pen.text((lx - nw / 2, ly - 7), num, font=num_font, fill=BLANK)


def draw_map(pen, left, top, wide, tall):
    """Stylised world map (equirectangular) with numbered pins 01-13."""
    fill_box(pen, left, top, wide, tall, OCEAN)
    lon0, lon1, lat0, lat1 = -180.0, 180.0, 78.0, -58.0

    def project(lon, lat):
        return (left + (lon - lon0) / (lon1 - lon0) * wide,
                top + (lat0 - lat) / (lat0 - lat1) * tall)

    for la in (60, 30, 0, -30):
        _, gy = project(0, la)
        pen.line([left, gy, left + wide, gy], fill=(190, 205, 220), width=1)
    for shape in SHORELINES:
        corners = [project(lon, lat) for lon, lat in shape]
        pen.polygon(corners, fill=(214, 208, 188), outline=(150, 144, 128))
    num_font = bold_face(10)
    for lon, lat, num, dx, dy in MAP_PINS:
        draw_pin(pen, project, num_font, num, lon, lat, dx, dy)


# ------------------------------------------------------------ page sections
# The page is laid out top to bottom: nameplate, figures, tallies,
# timeline, features, grid, map + digest, DATE CHECK, colophon.

def draw_nameplate(pen, left, width):
    """Top tag, paper name, dateline, standfirst, double rule."""
    pen.text((left, 10), "THE WORLD IN ONE DAY", font=bold_face(10), fill=MUTED)
    tag = "WEDNESDAY EDITION · No. 329"
    pen.text((left + width - pen.textlength(tag, font=bold_face(10)), 10),
              tag, font=bold_face(10), fill=MUTED)
    name = fit_typeface("DejaVuSerif-Bold.ttf", "THE WEDNESDAY PAPER", 64, width)
    pen.text((left, 24), "THE WEDNESDAY PAPER", font=name, fill=BODY)
    dateline = "WEDNESDAY 25 NOVEMBER 2026 — 36 STORIES, DATED HONESTLY"
    pen.text(((SHEET_W - pen.textlength(dateline, font=bold_face(12))) / 2, 92),
              dateline, font=bold_face(12), fill=ALERT)
    pen.line([left, 110, left + width, 110], fill=BODY, width=2)
    pen.line([left, 114, left + width, 114], fill=BODY, width=1)


def draw_figures(pen, left, y):
    """Six boxed headline figures with a two-line caption each."""
    cell, gap = 157, 6
    for i, (caption, figure) in enumerate(HEADLINES):
        x = left + i * (cell + gap)
        pen.rectangle([x, y, x + cell, y + 50], outline=RULE, width=1)
        fnt = fit_typeface("DejaVuSerif-Bold.ttf", figure, 26, cell - 12)
        fw = pen.textlength(figure, font=fnt)
        pen.text((x + (cell - fw) / 2, y + 4), figure, font=fnt, fill=ALERT)
        rows = fold_lines(pen, caption, bold_face(8), cell - 10)
        yy = y + 32
        for line in rows[:2]:
            lw = pen.textlength(line, font=bold_face(8))
            pen.text((x + (cell - lw) / 2, yy), line, font=bold_face(8),
                      fill=BODY)
            yy += 9


def draw_tallies(pen, left, y):
    """Coloured region tallies that add up to 36 stories."""
    x = left
    for n, name in TALLIES:
        label = "%s %d" % (name, n)
        fnt = bold_face(11)
        wid = int(pen.textlength(label, font=fnt)) + 22
        pen.rounded_rectangle([x, y, x + wid, y + 22], radius=11,
                               fill=paint_for_region(name))
        pen.text((x + 11, y + 5), label, font=fnt, fill=BLANK)
        x += wid + 8
    pen.text((x + 4, y + 5), "= 36 STORIES", font=body_face(11), fill=MUTED)


def draw_timeline(pen, left, y):
    """One-line UTC timeline of the day, shrunk until it fits."""
    size = 10
    while size > 7:
        fnt = body_face(size)
        if pen.textlength(DAY_LINE, font=fnt) <= CONTENT_W:
            break
        size -= 1
    pen.text((left, y), DAY_LINE, font=body_face(size), fill=DEEP_BLUE)


def draw_feature(pen, story, x, y, wid):
    """One feature story: artwork band, dateline, headline, deck."""
    num, kind, region, dateline, headline, deck, source = story
    art_h = 86
    scene_for_feature(kind)(pen, x, y, wid, art_h)
    pen.rectangle([x, y, x + wid, y + art_h], outline=RULE, width=1)
    yy = y + art_h + 6
    pen.text((x, yy), "%s  %s" % (num, dateline), font=bold_face(10),
              fill=ALERT)
    yy += 15
    _, yy = draw_lines(pen, (x, yy), headline, display_face(19), BODY, wid, gap=22, cap=2)
    _, yy = draw_lines(pen, (x, yy + 3), deck, body_face(11), BODY, wid, gap=13, cap=4)
    pen.text((x, yy + 4), source, font=body_face(9), fill=MUTED)


def draw_features(pen, left, y):
    """The three feature stories in a row."""
    wid, gap = 317, 12
    for i, story in enumerate(FEATURES):
        draw_feature(pen, story, left + i * (wid + gap), y, wid)


def draw_card(pen, story, x, y, wid, hei):
    """One small story card: region bar, vignette, number, texts."""
    num, kind, region, dateline, headline, deck, source = story
    pen.rectangle([x, y, x + wid, y + hei], fill=BLANK,
                   outline=RULE, width=1)
    pen.rectangle([x, y, x + wid, y + 3], fill=paint_for_region(region))
    scene_for_card(kind)(pen, x + 1, y + 4, wid - 2, 42)
    pen.rectangle([x + 1, y + 4, x + wid - 1, y + 46], outline=RULE,
                   width=1)
    ty = y + 50
    pen.text((x + 6, ty), num, font=bold_face(10), fill=ALERT)
    _, ty = draw_lines(pen, (x + 6, ty + 13), headline, bold_face(12), BODY,
                wid - 12, gap=13, cap=2)
    _, ty = draw_lines(pen, (x + 6, ty + 2), deck, body_face(10), BODY, wid - 12,
                gap=11, cap=2)
    pen.text((x + 6, y + hei - 11), source, font=body_face(8), fill=MUTED)


def draw_grid(pen, left, y):
    """Ten small stories in a 5 x 2 grid."""
    wid, gap, hei, rgap = 187, 10, 126, 6
    for i, story in enumerate(CARDS):
        row, col = divmod(i, 5)
        draw_card(pen, story, left + col * (wid + gap),
                   y + row * (hei + rgap), wid, hei)


def draw_map_block(pen, left, y):
    """Map heading, rules, the world map and its pin caption."""
    pen.text((left, y), "WHERE THE NEWS HAPPENED — STORIES 01–13",
              font=bold_face(11), fill=BODY)
    pen.text((384, y), "ALSO THIS WEEK — 23 MORE STORIES",
              font=bold_face(11), fill=BODY)
    pen.line([left, y + 16, left + 344, y + 16], fill=BODY, width=1)
    pen.line([384, y + 16, left + CONTENT_W, y + 16], fill=BODY, width=1)
    draw_map(pen, left, y + 20, 344, 172)
    pen.text((left, y + 196),
              "Pins: Riyadh · Langley · Brooklyn · Kyiv · Canberra · "
              "Paris · Washington",
              font=body_face(9), fill=MUTED)
    pen.text((left, y + 208),
              "Fort Hood · Warsaw · Carrara · Gaza · Rome · Copenhagen",
              font=body_face(9), fill=MUTED)


def draw_briefs(pen, _left, y):
    """The 23 briefs in two columns on the right."""
    col_x, col_w = 384, 300
    for i, (text, num) in enumerate(DIGEST):
        col, row = divmod(i, 12)
        bx = col_x + col * (col_w + 16)
        by = y + 22 + row * 15
        if pen.textlength(text, font=body_face(10)) > col_w - 20:
            raise ValueError("brief too long for one line: %r" % text)
        pen.text((bx, by), num, font=bold_face(10), fill=ALERT)
        pen.text((bx + 20, by), text, font=body_face(10), fill=BODY)


def draw_datecheck(pen, left, y):
    """The honesty strip: everything here is dated, not dressed up."""
    pen.line([left, y, left + CONTENT_W, y], fill=BODY, width=1)
    pen.text((left, y + 5), "DATE CHECK — ALSO THIS WEEK:",
              font=bold_face(10), fill=ALERT)
    draw_lines(pen, (left, y + 19), DATE_LINE, body_face(10), BODY, CONTENT_W, gap=13, cap=2)


def draw_colophon(pen, left):
    """Thin rule, sourcing note on the left, nameplate on the right."""
    pen.line([left, 1000, left + CONTENT_W, 1000], fill=RULE, width=1)
    pen.text((left, 1004),
              "Built 25 November 2026 from verified "
              "reports; figures as reported on the day.",
              font=body_face(9), fill=MUTED)
    right = "THE WEDNESDAY PAPER · 36 STORIES"
    pen.text((left + CONTENT_W - pen.textlength(right, font=bold_face(9)), 1004),
              right, font=bold_face(9), fill=MUTED)


# Sections driven by y position, in page order (nameplate and colophon
# are called directly: the nameplate needs the content width, the
# colophon is pinned to fixed y coordinates).
LAYOUT_STEPS = (
    (draw_figures, 122),
    (draw_tallies, 180),
    (draw_timeline, 208),
    (draw_features, 226),
    (draw_grid, 454),
    (draw_map_block, 720),
    (draw_briefs, 720),
    (draw_datecheck, 940),
)


def compose_sheet():
    """Draw every section onto a fresh 1024x1024 newsprint page."""
    img = Image.new("RGB", (SHEET_W, SHEET_H), NEWS_PRINT)
    pen = ImageDraw.Draw(img)
    draw_nameplate(pen, EDGE, CONTENT_W)
    for fn, y in LAYOUT_STEPS:
        fn(pen, EDGE, y)
    draw_colophon(pen, EDGE)
    return img


# ------------------------------------------------------------------- output

def _write_stored_copy():
    """Write the committed front page with stdlib only.

    Used when Pillow is missing (bare grade image) or the live draw
    fails. The picture bytes live in entry.png beside this file (it is
    committed in the repo); the sha256 and the 1 MiB cap are checked
    before writing.
    """
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(here, "entry.png")
    with open(src, "rb") as fh_in:
        data = fh_in.read()
    if hashlib.sha256(data).hexdigest() != FALLBACK_DIGEST:
        raise RuntimeError("stored copy sha256 mismatch")
    if len(data) > 1024 * 1024:
        raise RuntimeError("stored copy over the 1 MiB cap")
    os.makedirs(DEST_DIR, exist_ok=True)
    with open(DEST_PATH, "wb") as fh_out:
        fh_out.write(data)


def main():
    """Render the page (live draw, else stored copy) and save it."""
    assert len(FEATURES) + len(CARDS) + len(DIGEST) == 36, \
        "must be 36 stories"
    assert sum(n for n, _ in TALLIES) == 36, "tallies must sum to 36"
    if _CAN_DRAW:
        try:
            img = compose_sheet()
            os.makedirs(DEST_DIR, exist_ok=True)
            img.save(DEST_PATH, format="PNG", optimize=True)
            print("wrote %s (%dx%d) [live draw]"
                  % (DEST_PATH, SHEET_W, SHEET_H))
            return
        except Exception as exc:
            print("live draw failed (%s); using stored copy" % exc)
    _write_stored_copy()
    print("wrote %s (%dx%d) [pre-rendered]" % (DEST_PATH, SHEET_W, SHEET_H))


if __name__ == "__main__":
    main()
