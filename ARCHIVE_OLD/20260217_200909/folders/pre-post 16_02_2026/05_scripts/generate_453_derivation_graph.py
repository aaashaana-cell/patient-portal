#!/usr/bin/env python3
import csv
from pathlib import Path

BASE = Path('/Users/shanuakshah/Downloads/files (3)/pre-post 16_02_2026')
DATA = BASE / '04_datasets_mappings'
OUT = BASE / '01_interpretation_pack'


def read_summary(path):
    out = {}
    with open(path, newline='', encoding='utf-8') as f:
        r = csv.reader(f)
        for row in r:
            if len(row) >= 2:
                out[row[0]] = row[1]
    return out


def n_rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        return max(sum(1 for _ in f) - 1, 0)


def rect(x, y, w, h, fill, stroke='#234', rx=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'


def label(x, y, text, size=18, weight='600', fill='#0f172a', anchor='middle'):
    return f'<text x="{x}" y="{y}" font-family="Inter, Segoe UI, Arial" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{text}</text>'


def arrow(x1, y1, x2, y2, color='#334155'):
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2.2" marker-end="url(#arrow)"/>'


def main():
    s = read_summary(DATA / 'rerun2026_set_construction_summary.csv')
    pre_total = int(float(s['pre_total_rows']))
    responder_rows = int(float(s['colleague_responder_rows']))
    matched_unique = int(float(s['matched_pre_unique_rows']))
    non_all_summary = int(float(s['nonresponders_all_rows']))

    non_all = n_rows(DATA / 'rerun2026_nonresponder_all_standardized.csv')
    non_old = n_rows(DATA / 'rerun2026_nonresponder_oldlogic453_standardized.csv')
    removed_all3 = non_all - non_old

    # Use dataset-derived values when available
    non_all_rows = non_all if non_all > 0 else non_all_summary
    old_logic_rows = non_old

    w, h = 1200, 860

    b1 = (350, 40, 500, 100)
    b2 = (120, 220, 420, 130)
    b3 = (660, 220, 420, 130)
    b4 = (350, 430, 500, 130)
    b5 = (350, 640, 500, 130)

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">')
    svg.append('<defs><marker id="arrow" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#334155"/></marker></defs>')

    svg.append(rect(*b1, fill='#dbeafe'))
    svg.append(label(600, 78, 'Overall Pre-Assessment Dataset'))
    svg.append(label(600, 108, f'n = {pre_total}', size=28, weight='700', fill='#1d4ed8'))

    svg.append(rect(*b2, fill='#ecfccb'))
    svg.append(label(330, 258, 'Colleague Matched Responder File'))
    svg.append(label(330, 286, f'rows = {responder_rows}', size=22, weight='700', fill='#3f6212'))
    svg.append(label(330, 312, f'maps to unique pre rows = {matched_unique}', size=16, weight='500', fill='#365314'))

    svg.append(rect(*b3, fill='#fee2e2'))
    svg.append(label(870, 258, 'All Non-Responders (initial)'))
    svg.append(label(870, 286, f'n = {non_all_rows}', size=28, weight='700', fill='#b91c1c'))
    svg.append(label(870, 312, f'formula: {pre_total} - {matched_unique} = {non_all_rows}', size=16, weight='500', fill='#991b1b'))

    svg.append(rect(*b4, fill='#ffedd5'))
    svg.append(label(600, 468, 'Old-Logic Exclusion Step'))
    svg.append(label(600, 496, 'Remove rows where ALL 3 contact fields are missing'))
    svg.append(label(600, 524, f'(ID + Name + Email all blank) -> removed = {removed_all3}', size=20, weight='700', fill='#9a3412'))

    svg.append(rect(*b5, fill='#dcfce7'))
    svg.append(label(600, 678, 'Final Old-Logic Non-Responders'))
    svg.append(label(600, 708, f'n = {old_logic_rows}', size=34, weight='800', fill='#166534'))
    svg.append(label(600, 736, f'formula: {non_all_rows} - {removed_all3} = {old_logic_rows}', size=18, weight='600', fill='#14532d'))

    svg.append(arrow(600, 140, 330, 220))
    svg.append(arrow(600, 140, 870, 220))
    svg.append(arrow(870, 350, 600, 430))
    svg.append(arrow(600, 560, 600, 640))

    svg.append(label(600, 815, 'Derivation used for the 362 vs 453 analysis set', size=16, weight='500', fill='#334155'))

    svg.append('</svg>')

    svg_text = '\n'.join(svg)
    svg_path = OUT / 'GRAPH_Derivation_453_NonResponders.svg'
    svg_path.write_text(svg_text, encoding='utf-8')

    html = f'''<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>Derivation Graph: 453 Non-Responders</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Arial, sans-serif; margin: 20px; background: #f8fafc; color: #0f172a; }}
h1 {{ margin: 0 0 10px 0; }}
.note {{ margin: 6px 0 14px 0; color: #334155; }}
.card {{ background: white; border: 1px solid #dbe4ee; border-radius: 12px; padding: 10px; display: inline-block; }}
img {{ max-width: 100%; height: auto; }}
</style>
</head>
<body>
<h1>How 453 Non-Responders Were Derived</h1>
<div class="note">This graph documents the exact flow used for the old-logic non-responder definition.</div>
<div class="card">
<img src="GRAPH_Derivation_453_NonResponders.svg" alt="Derivation flow for 453 non-responders"/>
</div>
</body>
</html>
'''
    html_path = OUT / 'GRAPH_Derivation_453_NonResponders.html'
    html_path.write_text(html, encoding='utf-8')

    print(svg_path)
    print(html_path)


if __name__ == '__main__':
    main()
