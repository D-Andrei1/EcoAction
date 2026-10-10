"""
charts.py - draws simple, accessible charts as SVG (no chart library needed).
PROVIDED COMPLETE - type it in exactly and do not change it.
"""
import math
from ui import h
def _num(value):
    return ("%.2f" % value).rstrip("0").rstrip(".")

def line_chart(points, title, unit="kg CO2e", width=640, height=260):
    """points: list of (label, value) in time order, e.g. [("2026-W01", 6.4), ("2026-W02", 9.1)]"""
    if not points:
        return ""
    left, right, top, bottom = 56, 40, 16, 44
    plot_w, plot_h = width - left - right, height - top - bottom
    biggest = max(value for _, value in points) or 1.0
    step = plot_w / max(len(points) - 1, 1)
    parts = []
    for fraction in (0, 0.5, 1):
        y = top + plot_h - fraction * plot_h
        parts.append('<line class="gridline" x1="%d" x2="%d" y1="%.1f" y2="%.1f"/>'
                     % (left, width - right, y, y))
        parts.append('<text class="axis" x="%d" y="%.1f" text-anchor="end">%s</text>'
                     % (left - 6, y + 4, _num(biggest * fraction)))
    every = max(1, int(math.ceil(len(points) / 8.0)))
    coords = []

    for i, (label, value) in enumerate(points):
        x = left + i * step
        y = top + plot_h - (value / biggest) * plot_h
        coords.append("%.1f,%.1f" % (x, y))
        parts.append('<circle class="dot" cx="%.1f" cy="%.1f" r="3"><title>%s: %s %s</title></circle>'
                     % (x, y, h(label), _num(value), h(unit)))
        if i % every == 0:
            parts.append('<text class="axis" x="%.1f" y="%d" text-anchor="middle">%s</text>'
                        % (x, height - 18, h(label)))
    parts.insert(0, '<polyline class="line" points="%s"/>' % " ".join(coords))
    summary = "%s. %s" % (title, "; ".join("%s: %s %s" % (l, _num(v), unit) for l, v in points))
    return ('<figure class="chart"><svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>'
            '<figcaption>%s</figcaption></figure>' % (width, height, h(summary), "".join(parts), h(title)))

def bar_chart(items, title, unit="kg CO2e", width=640):
    """items: list of (label, value), e.g. [("transport", 20.0), ("energy", 8.5)]"""
    if not items:
        return ""
    row, label_w, value_w = 30, 130, 90
    height = row * len(items) + 10
    biggest = max(value for _, value in items) or 1.0
    bar_space = width - label_w - value_w
    parts = []
    for i, (label, value) in enumerate(items):
        y = 5 + i * row
        length = max(2.0, (value / biggest) * bar_space)
        parts.append('<text class="axis" x="%d" y="%d" text-anchor="end">%s</text>'
                     % (label_w - 8, y + 18, h(label)))
        parts.append('<rect class="bar" x="%d" y="%d" width="%.1f" height="20" rx="3"/>'
                     % (label_w, y + 4, length))
        parts.append('<text class="axis" x="%.1f" y="%d">%s</text>'
                     % (label_w + length + 6, y + 18, _num(value)))
    summary = "%s. %s" % (title, "; ".join("%s: %s %s" % (l, _num(v), unit) for l, v in items))
    return ('<figure class="chart"><svg viewBox="0 0 %d %d" role="img" aria-label="%s">%s</svg>'
    '<figcaption>%s</figcaption></figure>' % (width, height, h(summary), "".join(parts), h(title)))

def data_table(points, label_heading, value_heading):
    """The same numbers as a table, for people who can't see the chart (put it under every chart)."""
    rows = "".join("<tr><td>%s</td><td>%s</td></tr>" % (h(l), _num(v)) for l, v in points)
    return ('<details class="chart-data"><summary>Show the numbers</summary><table><thead><tr>'
            '<th scope="col">%s</th><th scope="col">%s</th></tr></thead><tbody>%s</tbody></table></details>'
            % (h(label_heading), h(value_heading), rows))