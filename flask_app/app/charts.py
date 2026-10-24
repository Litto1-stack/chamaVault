"""Hand-built inline SVG charts (no libraries). Colours come from CSS variables so theming stays in CSS."""
import math

from markupsafe import Markup, escape

PALETTE = ["var(--green)", "var(--terra)", "var(--amber)", "#5b8f78", "#d9a08f", "#8a7d6b"]


def area_chart(points, width=320, height=120) -> Markup:
    if len(points) < 2:
        return Markup("")
    lo, hi = min(points), max(points)
    span = (hi - lo) or 1
    xs = [i * width / (len(points) - 1) for i in range(len(points))]
    ys = [height - 8 - (p - lo) / span * (height - 24) for p in points]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in zip(xs, ys))
    area = f"0,{height} {line} {width},{height}"
    return Markup(
        f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" aria-label="Pool balance over time">'
        f'<polygon points="{area}" style="fill:var(--green);opacity:.15"/>'
        f'<polyline points="{line}" style="fill:none;stroke:var(--green);stroke-width:2.5;stroke-linejoin:round"/>'
        f'<circle cx="{xs[-1]:.1f}" cy="{ys[-1]:.1f}" r="4.5" style="fill:var(--terra)"/></svg>')


def bar_chart(bars, width=320, height=140) -> Markup:
    """bars: [(label, value, expected)] drawn as filled bars inside a faint 'expected' bar."""
    top = max([b[2] for b in bars] + [b[1] for b in bars] + [1])
    slot = width / len(bars)
    out = [f'<svg viewBox="0 0 {width} {height}" class="chart" role="img" aria-label="Collected versus expected per month">']
    for i, (label, value, expected) in enumerate(bars):
        x, w = i * slot + slot * 0.18, slot * 0.64
        eh, vh = expected / top * (height - 30), value / top * (height - 30)
        out.append(f'<rect x="{x:.1f}" y="{height - 20 - eh:.1f}" width="{w:.1f}" height="{eh:.1f}" rx="5" style="fill:var(--line)"/>')
        if vh:
            out.append(f'<rect x="{x:.1f}" y="{height - 20 - vh:.1f}" width="{w:.1f}" height="{vh:.1f}" rx="5" style="fill:var(--green)"/>')
        out.append(f'<text x="{x + w / 2:.1f}" y="{height - 5}" text-anchor="middle" style="fill:var(--muted);font-size:11px">{escape(label)}</text>')
    out.append("</svg>")
    return Markup("".join(out))


def donut(parts, size=140) -> Markup:
    """parts: [(label, value)]; returns the ring only (the template draws the legend)."""
    total = sum(v for _, v in parts) or 1
    r, c, offset = 52, 2 * math.pi * 52, 0.0
    segs = []
    for i, (_, v) in enumerate(parts):
        length = v / total * c
        segs.append(f'<circle cx="70" cy="70" r="{r}" fill="none" stroke-width="20" style="stroke:{PALETTE[i % len(PALETTE)]}" '
                    f'stroke-dasharray="{length:.2f} {c - length:.2f}" stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 70 70)"/>')
        offset += length
    return Markup(f'<svg viewBox="0 0 140 140" width="{size}" height="{size}" role="img" aria-label="Where the money came from">{"".join(segs)}</svg>')


def gauge(value, lo, hi) -> Markup:
    """Half-circle score gauge."""
    frac = max(0.0, min(1.0, (value - lo) / (hi - lo)))
    cx, cy, r = 110, 105, 85
    angle = math.pi * (1 - frac)
    x, y = cx + r * math.cos(angle), cy - r * math.sin(angle)
    track = f"M {cx - r} {cy} A {r} {r} 0 0 1 {cx + r} {cy}"
    fill = f"M {cx - r} {cy} A {r} {r} 0 0 1 {x:.1f} {y:.1f}"
    colour = "var(--green)" if value >= 600 else "var(--amber)" if value >= 500 else "var(--terra)"
    return Markup(
        f'<svg viewBox="0 0 220 120" class="gauge" role="img" aria-label="Credit score {value} on a scale of {lo} to {hi}">'
        f'<path d="{track}" style="fill:none;stroke:var(--line);stroke-width:16;stroke-linecap:round"/>'
        f'<path d="{fill}" style="fill:none;stroke:{colour};stroke-width:16;stroke-linecap:round"/>'
        f'<text x="{cx}" y="{cy - 12}" text-anchor="middle" style="fill:var(--ink);font-size:38px;font-weight:800">{value}</text>'
        f'<text x="{cx - r}" y="{cy + 14}" text-anchor="middle" style="fill:var(--muted);font-size:11px">{lo}</text>'
        f'<text x="{cx + r}" y="{cy + 14}" text-anchor="middle" style="fill:var(--muted);font-size:11px">{hi}</text></svg>')


def ring(pct, size=84) -> Markup:
    pct = max(0, min(100, pct))
    c = 2 * math.pi * 34
    return Markup(
        f'<svg viewBox="0 0 84 84" width="{size}" height="{size}" role="img" aria-label="{pct}% repaid">'
        f'<circle cx="42" cy="42" r="34" fill="none" stroke-width="9" style="stroke:var(--line)"/>'
        f'<circle cx="42" cy="42" r="34" fill="none" stroke-width="9" stroke-linecap="round" style="stroke:var(--green)" '
        f'stroke-dasharray="{pct / 100 * c:.1f} {c:.1f}" transform="rotate(-90 42 42)"/>'
        f'<text x="42" y="47" text-anchor="middle" style="fill:var(--ink);font-size:16px;font-weight:800">{pct}%</text></svg>')


def initials(name: str) -> str:
    return "".join(w[0] for w in name.split()[:2]).upper()


def avatar_color(member_id: int) -> str:
    return ["#1f6f4a", "#c4573a", "#b7791f", "#3f7f9a", "#7a5c8f", "#5b8f78"][member_id % 6]
