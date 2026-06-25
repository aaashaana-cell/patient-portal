#!/usr/bin/env python3
import csv
import math
from pathlib import Path

BASE = Path('/Users/shanuakshah/Downloads/files (3)/pre-post 16_02_2026')


def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, cols):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in cols})


def p_to_num(p):
    if p is None:
        return None
    p = str(p).strip()
    if not p or p == 'NA':
        return None
    if p.startswith('<'):
        try:
            return float(p[1:])
        except Exception:
            return 0.0
    try:
        return float(p)
    except Exception:
        return None


def is_sig(p):
    x = p_to_num(p)
    return (x is not None) and (x < 0.05)


def parse_npct(s):
    # format: "n (x.x%)"
    s = (s or '').strip()
    if '(' not in s or ')' not in s:
        return None, None
    try:
        n = int(s.split('(')[0].strip())
        pct_str = s.split('(')[1].split(')')[0].replace('%', '').strip()
        pct = float(pct_str)
        return n, pct
    except Exception:
        return None, None


def blank(v):
    v = (v or '').strip()
    return v == '' or v.upper() == 'NA'


def chi2(tab):
    r = len(tab)
    c = len(tab[0]) if r else 0
    row = [sum(tab[i]) for i in range(r)]
    col = [sum(tab[i][j] for i in range(r)) for j in range(c)]
    n = sum(row)
    val = 0.0
    for i in range(r):
        for j in range(c):
            exp = row[i] * col[j] / n if n else 0
            if exp > 0:
                val += (tab[i][j] - exp) ** 2 / exp
    return val, n, r, c


def cramers_v(tab):
    c2, n, r, c = chi2(tab)
    k = min(r - 1, c - 1)
    if n == 0 or k <= 0:
        return None
    return math.sqrt(c2 / (n * k))


def v_label(v):
    if v is None:
        return 'NA'
    if v < 0.1:
        return 'very small'
    if v < 0.3:
        return 'small'
    if v < 0.5:
        return 'moderate'
    return 'large'


def esc(x):
    x = str(x)
    return x.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def html_table(rows, cols, title=None):
    out = []
    if title:
        out.append(f'<h3>{esc(title)}</h3>')
    out.append('<table>')
    out.append('<thead><tr>' + ''.join(f'<th>{esc(c)}</th>' for c in cols) + '</tr></thead>')
    out.append('<tbody>')
    for r in rows:
        cls = ' class="sig"' if is_sig(r.get('p_value')) else ''
        out.append(f'<tr{cls}>')
        for c in cols:
            out.append(f'<td>{esc(r.get(c, ""))}</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


def build():
    # Source files (362 vs 453)
    levels = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_categorical_levels_labeled.csv')
    ctests = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_categorical_tests.csv')
    trn = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_training_checkbox_tests.csv')
    bar = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_barrier_checkbox_tests.csv')
    state_ext = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_state_rate_extremes_n_ge_10_labeled.csv')
    state_zero = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_state_no_matched_cases_labeled.csv')
    state_counts = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_state_counts_summary.csv')

    # 1) Caseload table
    caseload_rows = []
    for r in levels:
        if r.get('variable') == 'q0012':
            rn, rp = parse_npct(r.get('responder'))
            nn, np = parse_npct(r.get('nonresponder'))
            diff = '' if (rp is None or np is None) else f'{rp - np:+.1f} pp'
            caseload_rows.append({
                'caseload_level': r.get('level_label', r.get('level_code', '')),
                'responders_n_pct': r.get('responder', ''),
                'nonresponders_n_pct': r.get('nonresponder', ''),
                'difference_pp': diff,
                'test': r.get('test', ''),
                'p_value': r.get('p_value', ''),
                'interpretation': 'Distribution differs across caseload categories.' if is_sig(r.get('p_value')) else 'No significant distribution difference.'
            })

    # Cramer's V for caseload
    resp = read_csv(BASE / 'rerun2026_responder_362_standardized.csv')
    non = read_csv(BASE / 'rerun2026_nonresponder_oldlogic453_standardized.csv')
    lv = ['1', '2', '3', '4']
    rr = {k: 0 for k in lv}
    nnn = {k: 0 for k in lv}
    for r in resp:
        v = (r.get('q0012') or '').strip()
        if v in rr:
            rr[v] += 1
    for r in non:
        v = (r.get('q0012') or '').strip()
        if v in nnn:
            nnn[v] += 1
    tab = [[rr[k] for k in lv], [nnn[k] for k in lv]]
    caseload_v = cramers_v(tab)

    # 2) Training significant items
    training_sig = []
    for r in trn:
        if is_sig(r.get('p_value')):
            rn, rp = parse_npct(r.get('responder_selected'))
            nn, np = parse_npct(r.get('nonresponder_selected'))
            diff = '' if (rp is None or np is None) else f'{rp - np:+.1f} pp'
            training_sig.append({
                'training_item': r.get('label', ''),
                'responders_selected': r.get('responder_selected', ''),
                'nonresponders_selected': r.get('nonresponder_selected', ''),
                'difference_pp': diff,
                'test': r.get('test', ''),
                'p_value': r.get('p_value', ''),
                'interpretation': 'Higher in non-responders.' if (rp is not None and np is not None and np > rp) else 'Higher in responders.'
            })

    # 3) Barrier significant items
    barrier_sig = []
    for r in bar:
        if is_sig(r.get('p_value')):
            rn, rp = parse_npct(r.get('responder_selected'))
            nn, np = parse_npct(r.get('nonresponder_selected'))
            diff = '' if (rp is None or np is None) else f'{rp - np:+.1f} pp'
            direction = ''
            if rp is not None and np is not None:
                direction = 'Higher in responders.' if rp > np else 'Higher in non-responders.'
            barrier_sig.append({
                'barrier_item': r.get('label', ''),
                'responders_selected': r.get('responder_selected', ''),
                'nonresponders_selected': r.get('nonresponder_selected', ''),
                'difference_pp': diff,
                'test': r.get('test', ''),
                'p_value': r.get('p_value', ''),
                'interpretation': direction
            })

    # 4) State significance summary
    state_test = next((r for r in ctests if r.get('variable') == 'q0007'), None)

    state_levels = []
    for r in levels:
        if r.get('variable') == 'q0007':
            rn, rp = parse_npct(r.get('responder'))
            nn2, np2 = parse_npct(r.get('nonresponder'))
            if rn is None or nn2 is None:
                continue
            diff = None if (rp is None or np2 is None) else (rp - np2)
            state_levels.append({
                'state_name': r.get('level_label', ''),
                'responders_n_pct': r.get('responder', ''),
                'nonresponders_n_pct': r.get('nonresponder', ''),
                'difference_pp': '' if diff is None else f'{diff:+.1f} pp',
                'abs_diff': 0 if diff is None else abs(diff),
                'test': r.get('test', ''),
                'p_value': r.get('p_value', ''),
            })
    state_levels = sorted(state_levels, key=lambda x: x['abs_diff'], reverse=True)[:12]
    for r in state_levels:
        r['interpretation'] = 'Responder-heavy' if r['difference_pp'].startswith('+') else 'Non-responder-heavy'

    # state cramer's v
    # build contingency from standardized datasets
    resp_state = {}
    non_state = {}
    for r in resp:
        v = (r.get('q0007') or '').strip()
        if not blank(v):
            resp_state[v] = resp_state.get(v, 0) + 1
    for r in non:
        v = (r.get('q0007') or '').strip()
        if not blank(v):
            non_state[v] = non_state.get(v, 0) + 1
    keys = sorted(set(resp_state) | set(non_state), key=lambda x: float(x) if x.replace('.', '', 1).isdigit() else 9999)
    st_tab = [[resp_state.get(k, 0) for k in keys], [non_state.get(k, 0) for k in keys]]
    state_v = cramers_v(st_tab)

    # Write CSV tables
    write_csv(BASE / 'INTERPRETATION_PACK_01_GBV_Caseload_per_Week.csv', caseload_rows,
              ['caseload_level', 'responders_n_pct', 'nonresponders_n_pct', 'difference_pp', 'test', 'p_value', 'interpretation'])
    write_csv(BASE / 'INTERPRETATION_PACK_02_Training_Significant_Items.csv', training_sig,
              ['training_item', 'responders_selected', 'nonresponders_selected', 'difference_pp', 'test', 'p_value', 'interpretation'])
    write_csv(BASE / 'INTERPRETATION_PACK_03_Barrier_Significant_Items.csv', barrier_sig,
              ['barrier_item', 'responders_selected', 'nonresponders_selected', 'difference_pp', 'test', 'p_value', 'interpretation'])
    write_csv(BASE / 'INTERPRETATION_PACK_04_State_Key_Differences.csv', state_levels,
              ['state_name', 'responders_n_pct', 'nonresponders_n_pct', 'difference_pp', 'test', 'p_value', 'interpretation'])

    # Build HTML pack
    css = """
    <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; margin: 24px; color: #142433; background:#f6f9fc; }
    h1 { margin:0 0 8px 0; }
    h2 { margin:24px 0 8px 0; }
    h3 { margin:14px 0 6px 0; }
    .small { color:#486581; font-size:12px; }
    .note { background:#fff8e1; border:1px solid #f1d18a; border-radius:8px; padding:10px; }
    .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; margin:10px 0 16px 0; }
    .card { background:white; border:1px solid #dbe4ee; border-radius:8px; padding:10px; }
    .k { font-size:12px; color:#5b6e81; }
    .v { font-size:20px; font-weight:700; margin-top:4px; }
    table { border-collapse:collapse; width:100%; background:white; border:1px solid #dbe4ee; font-size:12px; }
    th, td { border:1px solid #e5ecf3; padding:6px 8px; vertical-align:top; }
    th { background:#eef4fa; text-align:left; }
    tr.sig td { background:#fff7e8; }
    </style>
    """

    state_p = state_test.get('p_value', '') if state_test else 'NA'
    state_test_name = state_test.get('test', '') if state_test else 'NA'
    state_interp = state_test.get('interpretation', '') if state_test else ''

    html = []
    html.append('<!doctype html><html><head><meta charset="utf-8"><title>Interpretation Table Pack (362 vs 453)</title>')
    html.append(css)
    html.append('</head><body>')
    html.append('<h1>Interpretation Table Pack: 362 Responders vs 453 Non-Responders</h1>')
    html.append('<p class="small">Source set: old-logic non-responders (rows with all 3 contact fields missing excluded).</p>')
    html.append('<div class="note"><strong>How to read significance:</strong> p&lt;0.05 indicates evidence of a between-group distribution difference. It does not prove causality. Effect size (Cram\'ers V) helps judge magnitude.</div>')

    html.append('<h2>1) GBV Caseload per Week</h2>')
    html.append('<div class="cards">')
    html.append(f'<div class="card"><div class="k">Test</div><div class="v">Chi-square</div></div>')
    html.append(f'<div class="card"><div class="k">p-value</div><div class="v">0.0494</div></div>')
    html.append(f'<div class="card"><div class="k">Effect size (Cram\'ers V)</div><div class="v">{caseload_v:.3f}</div><div class="small">{v_label(caseload_v)} effect</div></div>')
    html.append('</div>')
    html.append(html_table(caseload_rows, ['caseload_level', 'responders_n_pct', 'nonresponders_n_pct', 'difference_pp', 'test', 'p_value', 'interpretation']))

    html.append('<h2>2) Training Item (Significant)</h2>')
    html.append(html_table(training_sig, ['training_item', 'responders_selected', 'nonresponders_selected', 'difference_pp', 'test', 'p_value', 'interpretation']))

    html.append('<h2>3) Barrier Items (Significant)</h2>')
    html.append(html_table(barrier_sig, ['barrier_item', 'responders_selected', 'nonresponders_selected', 'difference_pp', 'test', 'p_value', 'interpretation']))

    html.append('<h2>4) State</h2>')
    html.append('<div class="cards">')
    html.append(f'<div class="card"><div class="k">Test</div><div class="v">{esc(state_test_name)}</div></div>')
    html.append(f'<div class="card"><div class="k">p-value</div><div class="v">{esc(state_p)}</div></div>')
    html.append(f'<div class="card"><div class="k">Effect size (Cram\'ers V)</div><div class="v">{state_v:.3f}</div><div class="small">{v_label(state_v)} effect</div></div>')
    html.append('</div>')
    html.append(f'<p class="small">Interpretation: {esc(state_interp)}</p>')
    html.append(html_table(state_levels, ['state_name', 'responders_n_pct', 'nonresponders_n_pct', 'difference_pp', 'interpretation', 'p_value'], title='Top State Distribution Differences (by absolute percentage-point gap)'))
    html.append(html_table(state_ext, ['metric', 'state_name', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct'], title='Highest/Lowest Completion Rate (states with total n >= 10)'))
    html.append(html_table(state_zero, ['state_name', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct'], title='States with No Matched Cases'))
    html.append(html_table(state_counts, ['metric', 'value'], title='State Coverage Summary'))

    html.append('</body></html>')

    (BASE / 'FINAL_Interpretation_Table_Pack_362v453.html').write_text('\n'.join(html), encoding='utf-8')


if __name__ == '__main__':
    build()
    print('Interpretation table pack generated.')
