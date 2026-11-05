#!/usr/bin/env python3
"""Генератор карточек статистики GitHub в стиле личного сайта.

Данные берутся из GraphQL API (файл stats.json), рендерятся в SVG.
Текст — в кривых (Inter), поэтому не зависит от внешних сервисов и шрифтов.

Использование:
    python tools/make_stats.py <stats.json> <output_dir>
"""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.misc.transform import Transform

BG = "#11131c"
BORDER = "#2a2f45"
FG = "#e7e9f3"
MUTED = "#8b93b0"
DIM = "#5a6280"
ACCENT = "#41cd52"
ACCENT2 = "#5865f2"

FONT_CANDIDATES = [
    Path("C:/Users/Daka/AppData/Local/Temp/opencode/inter/extras/ttf/Inter-SemiBold.ttf"),
    Path("C:/Users/Daka/AppData/Local/Temp/opencode/inter/extras/ttf/Inter-Medium.ttf"),
    Path("/usr/share/fonts/truetype/inter/Inter-SemiBold.ttf"),
]

LANG_COLORS = {
    "Python": "#3776AB", "HTML": "#E34C26", "CSS": "#563D7C",
    "JavaScript": "#F7DF1E", "TypeScript": "#3178C6", "Shell": "#89E051",
    "Batchfile": "#C1F12E", "Dockerfile": "#384D54", "Kotlin": "#A97BFF",
    "Java": "#B07219", "C++": "#F34B7D", "C": "#555555", "Rust": "#DEA584",
    "Go": "#00ADD8", "Ruby": "#701516", "PHP": "#4F5D95",
}


class Font:
    def __init__(self) -> None:
        for p in FONT_CANDIDATES:
            if p.exists():
                self.tt = TTFont(str(p))
                break
        else:
            raise SystemExit("Inter font not found")
        self.gset = self.tt.getGlyphSet()
        self.cmap = self.tt.getBestCmap()
        self.upem = self.tt["head"].unitsPerEm

    def width(self, text: str, size: float) -> float:
        total = 0.0
        for ch in text:
            name = self.cmap.get(ord(ch))
            if name:
                total += self.gset[name].width
            else:
                total += self.upem * 0.5
        return total * size / self.upem

    def path(self, text: str, x: float, baseline: float, size: float) -> str:
        scale = size / self.upem
        parts: list[str] = []
        cursor = 0.0
        for ch in text:
            name = self.cmap.get(ord(ch))
            if name:
                g = self.gset[name]
                spen = SVGPathPen(self.gset)
                g.draw(TransformPen(spen, Transform(scale, 0, 0, -scale, x + cursor * scale, baseline)))
                d = spen.getCommands()
                if d:
                    parts.append(d)
                cursor += g.width
            else:
                cursor += self.upem * 0.5
        return " ".join(parts)


FONT = Font()


def label(x: float, y: float, text: str, size: float, color: str) -> str:
    d = FONT.path(text, x, y + size * 0.35, size)
    return f'<path d="{d}" fill="{color}"/>' if d else ""


def card(width: int, height: int, inner: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{BG}" stroke="{BORDER}"/>
{inner}
</svg>
"""


def stat_row(x: float, y: float, icon_path: str, text: str, value: str, color: str) -> str:
    parts = [f'<g transform="translate({x},{y - 9}) scale(0.75)" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{icon_path}</g>']
    parts.append(label(x + 26, y, text, 13, MUTED))
    vd = FONT.path(value, x + 150, y + 13 * 0.35, 14)
    parts.append(f'<path d="{vd}" fill="{FG}"/>')
    return "".join(parts)


ICONS = {
    "star": '<path d="M12 2l3 7 7 .5-5.5 4.5 2 7-6.5-4-6.5 4 2-7L2 9.5 9 9z"/>',
    "repo": '<path d="M4 4a2 2 0 0 1 2-2h12v18H6a2 2 0 0 0-2 2z"/><path d="M4 20a2 2 0 0 1 2-2h12"/>',
    "users": '<path d="M17 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9.5" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.9"/>',
    "commit": '<circle cx="12" cy="12" r="3.5"/><path d="M12 2v6.5M12 15.5V22"/>',
    "pr": '<circle cx="6" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M6 9v6M18 9v3a3 3 0 0 1-3 3h-3"/><circle cx="18" cy="6" r="3"/>',
    "fire": '<path d="M12 2s5 5 5 10a5 5 0 0 1-10 0c0-2 1-3 1-3s1 1 2 1c0-3-3-4-3-4s5-2 5-4z"/>',
}


def make_overview(stats: dict, out: Path) -> None:
    W, H = 420, 220
    parts = [f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>']
    parts.append(label(24, 36, "GitHub Stats", 16, FG))
    parts.append(f'<path d="M24 46 h{W-48}" stroke="{BORDER}"/>')

    rows = [
        ("star", "Total stars", str(stats["stars"]), ACCENT),
        ("repo", "Repositories", str(stats["repos"]), ACCENT2),
        ("users", "Followers", str(stats["followers"]), "#26A5E4"),
        ("commit", "Commits (year)", str(stats["commits"]), "#E6522C"),
        ("pr", "Pull requests", str(stats["prs"]), "#A371F7"),
    ]
    y = 76
    for icon, text, value, color in rows:
        parts.append(stat_row(30, y, ICONS[icon], text, value, color))
        y += 27
    (out / "stats-overview.svg").write_text(card(W, H, "\n".join(parts[1:])), encoding="utf-8")
    print("stats-overview.svg")


def make_langs(stats: dict, out: Path) -> None:
    langs = stats["langs"]
    total = sum(langs.values()) or 1
    items = sorted(langs.items(), key=lambda kv: kv[1], reverse=True)[:6]

    W, H = 420, 220
    parts = [label(24, 36, "Top Languages", 16, FG), f'<path d="M24 46 h{W-48}" stroke="{BORDER}"/>']

    # сегментная полоса
    bar_y = 62
    bar_h = 10
    x = 24
    usable = W - 48
    for name, size in items:
        w = usable * size / total
        color = LANG_COLORS.get(name, MUTED)
        parts.append(f'<rect x="{x:.1f}" y="{bar_y}" width="{max(w - 1.5, 0):.1f}" height="{bar_h}" rx="3" fill="{color}"/>')
        x += w

    y = bar_y + bar_h + 34
    for name, size in items:
        pct = size / total * 100
        color = LANG_COLORS.get(name, MUTED)
        parts.append(f'<circle cx="30" cy="{y - 4}" r="5" fill="{color}"/>')
        parts.append(label(44, y, name, 13.5, FG))
        pd = FONT.path(f"{pct:.1f}%", W - 24 - FONT.width(f"{pct:.1f}%", 13), y + 13 * 0.35, 13)
        parts.append(f'<path d="{pd}" fill="{MUTED}"/>')
        y += 26

    (out / "stats-langs.svg").write_text(card(W, H, "\n".join(parts)), encoding="utf-8")
    print("stats-langs.svg")


def make_streak(stats: dict, out: Path) -> None:
    W, H = 856, 150
    parts = [label(28, 36, "Current streak", 12, MUTED), label(28, 66, f"{stats['current_streak']} days", 22, ACCENT)]
    parts.append(label(300, 36, "Longest streak", 12, MUTED))
    parts.append(label(300, 66, f"{stats['longest_streak']} days", 22, "#E6522C"))
    parts.append(label(572, 36, "Contributions", 12, MUTED))
    parts.append(label(572, 66, f"{stats['total_contrib']}", 22, ACCENT2))
    parts.append(label(760, 36, "This year", 12, MUTED))
    parts.append(label(760, 66, f"{stats['contrib_year']}", 22, "#26A5E4"))

    # искра по дням
    days = stats["days"][-140:]
    if days:
        maxc = max(days) or 1
        sx, sy, sw, sh = 28, 96, W - 56, 34
        step = sw / max(len(days) - 1, 1)
        pts = []
        for i, c in enumerate(days):
            px = sx + i * step
            py = sy + sh - (c / maxc) * sh
            pts.append(f"{px:.1f},{py:.1f}")
        parts.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linejoin="round"/>')
        parts.append(f'<polyline points="{sx},{sy+sh} {" ".join(pts)} {sx+sw},{sy+sh}" fill="{ACCENT}" fill-opacity="0.10" stroke="none"/>')

    (out / "stats-streak.svg").write_text(card(W, H, "\n".join(parts)), encoding="utf-8")
    print("stats-streak.svg")


def make_activity(stats: dict, out: Path) -> None:
    """Полный календарь вкладов за год (53 недели)."""
    days = stats["days"]
    W, H = 856, 150
    cell, gap = 11, 3
    # 53 недели -> ширина
    start_x = 30
    start_y = 56
    parts = [label(28, 34, "Contributions in the last year", 15, FG)]

    # разбиваем на недели по 7
    weeks: list[list[int]] = []
    chunk: list[int] = []
    for d in days:
        chunk.append(d)
        if len(chunk) == 7:
            weeks.append(chunk)
            chunk = []
    if chunk:
        weeks.append(chunk)

    maxc = max(days) or 1
    def level(c: int) -> str:
        if c == 0:
            return "#1b1f2e"
        r = c / maxc
        if r < 0.25: return "#1f5c2a"
        if r < 0.5: return "#2c8f3d"
        if r < 0.75: return "#38b24b"
        return ACCENT

    for wi, week in enumerate(weeks):
        for di, c in enumerate(week):
            x = start_x + wi * (cell + gap)
            y = start_y + di * (cell + gap)
            parts.append(f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" fill="{level(c)}"/>')

    total_w = len(weeks) * (cell + gap)
    parts.append(label(start_x, H - 20, f"{stats['total_contrib']} contributions", 12, MUTED))
    parts.append(f'<circle cx="{start_x + total_w - 90}" cy="{H - 24}" r="5" fill="#1f5c2a"/>')
    parts.append(f'<circle cx="{start_x + total_w - 70}" cy="{H - 24}" r="5" fill="#38b24b"/>')
    parts.append(f'<circle cx="{start_x + total_w - 50}" cy="{H - 24}" r="5" fill="{ACCENT}"/>')

    (out / "stats-activity.svg").write_text(card(W, H, "\n".join(parts)), encoding="utf-8")
    print("stats-activity.svg")


def main() -> None:
    stats_path = Path(sys.argv[1])
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    raw = json.loads(stats_path.read_text(encoding="utf-8"))
    u = raw["data"]["user"]
    repos = u["repositories"]["nodes"]

    langs: dict[str, int] = {}
    for r in repos:
        for e in (r.get("languages") or {}).get("edges", []):
            name = e["node"]["name"]
            langs[name] = langs.get(name, 0) + e["size"]

    days_raw = u["contributionsCollection"]["contributionCalendar"]["weeks"]
    flat: list[int] = []
    for w in days_raw:
        for d in w["contributionDays"]:
            flat.append(d["contributionCount"])

    # серии
    cur = longest = 0
    for c in flat:
        if c > 0:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 0

    stats = {
        "followers": u["followers"]["totalCount"],
        "repos": u["repositories"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "prs": u["contributionsCollection"]["totalPullRequestContributions"],
        "total_contrib": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "contrib_year": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "current_streak": cur,
        "longest_streak": longest,
        "langs": langs,
        "days": flat,
    }

    make_overview(stats, out)
    make_langs(stats, out)
    make_streak(stats, out)
    make_activity(stats, out)


if __name__ == "__main__":
    main()