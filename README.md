# THE WEDNESDAY PAPER

[![news-image-20261125](https://make.fun/badge/news-image-20261125.svg)](https://make.fun/bounty/news-image-20261125)
[![rank](https://make.fun/badge/news-image-20261125/keepomakima/news-image-20261125/rank.svg)](https://make.fun/bounty/news-image-20261125)
[![reward](https://make.fun/badge/news-image-20261125/keepomakima/news-image-20261125/reward.svg)](https://make.fun/bounty/news-image-20261125)

Wednesday 25 November 2026 in a single picture: 36 world stories, each
checked against at least two independent sources, set out as a newspaper
front page — a dated nameplate, six headline figures, region tallies, a
short UTC timeline, three illustrated feature stories, ten small panels,
a numbered world map, twenty-three one-line briefs, and a DATE CHECK
strip that dates every older event honestly instead of passing it off as
Wednesday news.

## The three features

- **Riyadh** — a Houthi drone hits the 385 m PIF Tower, the second strike
  in under a week; 11 wounded.
- **Washington** — hackers breach CIA and ODNI systems, exposing
  unclassified data.
- **Brooklyn** — a jury finds Huawei guilty on 10 of 12 counts.

Two items are genuinely Wednesday-fresh: Australia's October CPI
(+4.9%) at 07:30 WIB and the Shenzhou-24 launch carrying the first
foreign astronaut to China's Tiangong station.

## Build

```sh
python3 main.py
```

Writes `entry.png` (1024×1024, under 1 MiB) to `$MAKEFUN_OUTPUT_DIR`
(`/output` by default). The page is drawn with Pillow; the grading
machine runs bare Python 3.13 with no Pillow, so when Pillow is missing
(or the live draw fails) `main.py` falls back to a pre-rendered copy of
the same picture stored inside `main.py` as a compressed blob, verified
by sha256 — standard library only, no network.

Every story is sourced in `SOURCES-v1.md` in the work directory; the
DATE CHECK strip on the page lists the events that are easy to mis-date
(COP31 fell Sunday, Sparta II was hit Saturday, the first PIF Tower
strike was Thursday, and so on).

## Licence

MIT — see `LICENSE`.
