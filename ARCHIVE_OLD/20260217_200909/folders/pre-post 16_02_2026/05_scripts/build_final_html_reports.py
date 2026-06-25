#!/usr/bin/env python3
import csv
from pathlib import Path

BASE = Path('/Users/shanuakshah/Downloads/files (3)/pre-post 16_02_2026')


def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def read_text_lines(path):
    with open(path, encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def load_state_map():
    rows = read_csv(BASE / 'state_code_mapping_full_from_sav.csv')
    return {str(r['state_code']).strip(): r['state_name'] for r in rows}


def label_state_rows(rows, code_col='state_code'):
    smap = load_state_map()
    out = []
    for r in rows:
        z = dict(r)
        code = str(z.get(code_col, '')).strip()
        z['state_name'] = smap.get(code, z.get('state_name', code))
        out.append(z)
    return out


def label_state_levels(rows):
    smap = load_state_map()
    out = []
    for r in rows:
        z = dict(r)
        if z.get('variable') == 'q0007':
            code = str(z.get('level_code', '')).strip()
            if code in smap:
                z['level_label'] = smap[code]
        out.append(z)
    return out


def p_value_num(p):
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


def sig_class(p):
    pn = p_value_num(p)
    if pn is not None and pn < 0.05:
        return 'sig'
    return ''


def parse_pct(s):
    s = (s or '').strip()
    if s.endswith('%'):
        try:
            return float(s[:-1])
        except Exception:
            return None
    return None


def bar_html(pct):
    if pct is None:
        return ''
    pct = max(0.0, min(100.0, pct))
    return (
        f'<div class="bar-wrap"><div class="bar-fill" style="width:{pct:.1f}%"></div>'
        f'<span class="bar-text">{pct:.1f}%</span></div>'
    )


def table_html(rows, columns, title=None, sig_p_col=None, pct_bar_cols=None):
    if pct_bar_cols is None:
        pct_bar_cols = set()
    out = []
    if title:
        out.append(f'<h3>{title}</h3>')
    if not rows:
        out.append('<p><em>No data.</em></p>')
        return '\n'.join(out)
    out.append('<table>')
    out.append('<thead><tr>' + ''.join(f'<th>{c}</th>' for c in columns) + '</tr></thead>')
    out.append('<tbody>')
    for r in rows:
        row_cls = ''
        if sig_p_col:
            row_cls = sig_class(r.get(sig_p_col))
        out.append(f'<tr class="{row_cls}">')
        for c in columns:
            v = r.get(c, '')
            cell = f'{v}'
            if c in pct_bar_cols:
                pct = parse_pct(v)
                if pct is not None:
                    cell = f'{v}{bar_html(pct)}'
            out.append(f'<td>{cell}</td>')
        out.append('</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


CSS = """
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 24px; color: #132238; background: #f7fafc; }
h1 { margin: 0 0 8px 0; font-size: 28px; }
h2 { margin: 28px 0 10px 0; font-size: 20px; }
h3 { margin: 20px 0 8px 0; font-size: 16px; }
p, li { line-height: 1.45; }
.card-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 10px; margin: 10px 0 18px; }
.card { background: #ffffff; border: 1px solid #d9e2ec; border-radius: 10px; padding: 10px 12px; }
.card .k { font-size: 12px; color: #486581; }
.card .v { font-size: 18px; font-weight: 700; margin-top: 4px; }
.note { background: #fff8e1; border: 1px solid #f0d17a; border-radius: 10px; padding: 10px 12px; }
table { border-collapse: collapse; width: 100%; background: white; border: 1px solid #d9e2ec; font-size: 12px; }
th, td { border: 1px solid #e4ebf2; padding: 6px 8px; vertical-align: top; }
th { background: #f0f4f8; text-align: left; position: sticky; top: 0; }
tr.sig td { background: #fff7e6; }
.bar-wrap { margin-top: 4px; position: relative; height: 10px; background: #eaf0f6; border-radius: 999px; }
.bar-fill { height: 10px; background: linear-gradient(90deg, #2bb0ed, #0b5fff); border-radius: 999px; }
.bar-text { display: none; }
hr { border: 0; border-top: 1px solid #d9e2ec; margin: 20px 0; }
.small { font-size: 12px; color: #486581; }
a { color: #0b5fff; text-decoration: none; }
a:hover { text-decoration: underline; }
</style>
"""


def build_analysis1_html():
    summary = read_csv(BASE / 'rerun2026_analysis1_nonresponder_missing_data_summary.csv')
    detail = read_csv(BASE / 'rerun2026_analysis1_nonresponder_missing_data_table.csv')
    lines = read_text_lines(BASE / 'rerun2026_analysis1_summary.txt')
    age = read_csv(BASE / 'rerun2026_analysis2_all512_age_numeric_test.csv')
    ctests = read_csv(BASE / 'rerun2026_analysis2_all512_categorical_tests.csv')
    clevels = label_state_levels(read_csv(BASE / 'rerun2026_analysis2_all512_categorical_levels.csv'))
    trn = read_csv(BASE / 'rerun2026_analysis2_all512_training_checkbox_tests.csv')
    bar = read_csv(BASE / 'rerun2026_analysis2_all512_barrier_checkbox_tests.csv')
    conf = read_csv(BASE / 'rerun2026_analysis2_all512_confidence_item_tests.csv')
    confo = read_csv(BASE / 'rerun2026_analysis2_all512_confidence_overall_test.csv')
    know = read_csv(BASE / 'rerun2026_analysis2_all512_knowledge_numeric_tests.csv')
    s_top = label_state_rows(read_csv(BASE / 'rerun2026_analysis2_all512_state_top_completers.csv'))
    s_zero = label_state_rows(read_csv(BASE / 'rerun2026_analysis2_all512_state_no_matched_cases.csv'))
    s_ext = label_state_rows(read_csv(BASE / 'rerun2026_analysis2_all512_state_rate_extremes_n_ge_10.csv'))
    s_cnt = read_csv(BASE / 'rerun2026_analysis2_all512_state_counts_summary.csv')
    lines_full = read_text_lines(BASE / 'rerun2026_analysis2_all512_summary.txt')

    cards = []
    for r in summary:
        cards.append(f"<div class='card'><div class='k'>{r['metric']}</div><div class='v'>{r['n']} / {r['total_n']} ({r['pct']})</div></div>")
    if age:
        cards.append(f"<div class='card'><div class='k'>Age test</div><div class='v'>p={age[0]['p_value']}</div></div>")
    for r in ctests:
        if sig_class(r.get('p_value')):
            cards.append(f"<div class='card'><div class='k'>{r['label']}</div><div class='v'>p={r['p_value']}</div></div>")

    html = []
    html.append('<!doctype html><html><head><meta charset="utf-8"><title>Final Analysis 1 (362 vs 512)</title>')
    html.append(CSS)
    html.append('</head><body>')
    html.append('<h1>Final Analysis 1: Responder 362 vs All Non-Responders 512</h1>')
    html.append('<p class="small">Includes both missing-data profile and full demographic/statistical comparison.</p>')
    html.append('<div class="card-grid">' + ''.join(cards) + '</div>')
    html.append('<h2>A. Missing Data Profile</h2>')
    html.append(table_html(detail, ['variable', 'label', 'missing_n', 'total_n', 'missing_pct'], title='Field-Level Missingness', pct_bar_cols={'missing_pct'}))
    html.append(table_html(summary, ['metric', 'n', 'total_n', 'pct'], title='Combined Missingness Metrics', pct_bar_cols={'pct'}))
    html.append('<h2>B. Demographic and Response-Related Differences</h2>')
    html.append(table_html(age, ['label', 'responder_n', 'responder_mean', 'responder_sd', 'nonresponder_n', 'nonresponder_mean', 'nonresponder_sd', 'test', 'p_value', 'interpretation'], title='Age', sig_p_col='p_value'))
    html.append(table_html(ctests, ['label', 'test', 'p_value', 'interpretation'], title='Core Demographic/Knowledge Tests', sig_p_col='p_value'))
    html.append(table_html(clevels, ['label', 'level_label', 'responder', 'nonresponder', 'test', 'p_value'], title='Category Distributions (State labels from SAV)', sig_p_col='p_value'))
    html.append(table_html(trn, ['label', 'responder_selected', 'nonresponder_selected', 'test', 'p_value', 'interpretation'], title='Formal Training in GBV Handling (Q0010)', sig_p_col='p_value'))
    html.append(table_html(bar, ['label', 'responder_selected', 'nonresponder_selected', 'test', 'p_value', 'interpretation'], title='Barriers (Q0013)', sig_p_col='p_value'))
    html.append(table_html(conf, ['label', 'responder_mean', 'nonresponder_mean', 'test', 'p_value', 'interpretation'], title='Confidence Items (Q0014)', sig_p_col='p_value'))
    html.append(table_html(confo, ['label', 'responder_mean', 'nonresponder_mean', 'test', 'p_value', 'interpretation'], title='Overall Confidence'))
    html.append(table_html(know, ['label', 'responder_mean', 'nonresponder_mean', 'test', 'p_value', 'interpretation'], title='Knowledge Numeric Scores (Q0015-Q0017)', sig_p_col='p_value'))
    html.append('<h2>C. State Patterns</h2>')
    html.append(table_html(s_top, ['state_name', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct'], title='States with Largest Absolute Completer Counts', pct_bar_cols={'completion_rate_pct'}))
    html.append(table_html(s_zero, ['state_name', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct'], title='States with No Matched Cases'))
    html.append(table_html(s_ext, ['metric', 'state_name', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct'], title='Highest/Lowest Completion Rates (n>=10)', pct_bar_cols={'completion_rate_pct'}))
    html.append(table_html(s_cnt, ['metric', 'value'], title='State Coverage Summary'))
    html.append('<h2>Interpretation</h2>')
    html.append('<p><strong>Missingness findings:</strong></p>')
    html.append('<ul>' + ''.join(f'<li>{x}</li>' for x in lines) + '</ul>')
    html.append('<p><strong>Demographic/statistical findings:</strong></p>')
    html.append('<ul>' + ''.join(f'<li>{x}</li>' for x in lines_full) + '</ul>')
    html.append('</body></html>')

    out = BASE / 'FINAL_Analysis1_Responder362_vs_AllNonResponders512.html'
    out.write_text('\n'.join(html), encoding='utf-8')


def build_analysis2_html():
    age = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_age_numeric_test.csv')
    ctests = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_categorical_tests.csv')
    clevels = label_state_levels(read_csv(BASE / 'rerun2026_analysis2_oldlogic453_categorical_levels_labeled.csv'))
    trn = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_training_checkbox_tests.csv')
    bar = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_barrier_checkbox_tests.csv')
    conf = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_confidence_item_tests.csv')
    confo = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_confidence_overall_test.csv')
    know = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_knowledge_numeric_tests.csv')
    s_top = label_state_rows(read_csv(BASE / 'rerun2026_analysis2_oldlogic453_state_top_completers_labeled.csv'))
    s_zero = label_state_rows(read_csv(BASE / 'rerun2026_analysis2_oldlogic453_state_no_matched_cases_labeled.csv'))
    s_ext = label_state_rows(read_csv(BASE / 'rerun2026_analysis2_oldlogic453_state_rate_extremes_n_ge_10_labeled.csv'))
    s_cnt = read_csv(BASE / 'rerun2026_analysis2_oldlogic453_state_counts_summary.csv')
    lines = read_text_lines(BASE / 'rerun2026_analysis2_oldlogic453_summary.txt')

    sig_cards = []
    if age:
        a = age[0]
        sig_cards.append(f"<div class='card'><div class='k'>Age</div><div class='v'>p={a['p_value']}</div><div class='small'>{a['interpretation']}</div></div>")
    for r in ctests:
        if sig_class(r.get('p_value')):
            sig_cards.append(f"<div class='card'><div class='k'>{r['label']}</div><div class='v'>p={r['p_value']}</div><div class='small'>{r['test']}</div></div>")
    for r in trn:
        if sig_class(r.get('p_value')):
            sig_cards.append(f"<div class='card'><div class='k'>Training item</div><div class='v'>p={r['p_value']}</div><div class='small'>{r['label']}</div></div>")
    for r in bar:
        if sig_class(r.get('p_value')):
            sig_cards.append(f"<div class='card'><div class='k'>Barrier item</div><div class='v'>p={r['p_value']}</div><div class='small'>{r['label']}</div></div>")

    html = []
    html.append('<!doctype html><html><head><meta charset="utf-8"><title>Final Analysis 2 (362 vs 453)</title>')
    html.append(CSS)
    html.append('</head><body>')
    html.append('<h1>Final Analysis 2: Responder 362 vs Non-Responders 453</h1>')
    html.append('<p class="small">Non-responder definition: excluded rows where ID, name, and email are all missing (old logic).</p>')

    if sig_cards:
        html.append('<h2>Key Significant Findings</h2><div class="card-grid">' + ''.join(sig_cards) + '</div>')

    html.append(table_html(age, ['label', 'responder_n', 'responder_mean', 'responder_sd', 'nonresponder_n', 'nonresponder_mean', 'nonresponder_sd', 'test', 'p_value', 'interpretation'], title='Age', sig_p_col='p_value'))
    html.append(table_html(ctests, ['label', 'test', 'p_value', 'interpretation'], title='Core Demographic/Knowledge Tests', sig_p_col='p_value'))
    html.append(table_html(clevels, ['label', 'level_label', 'responder', 'nonresponder', 'test', 'p_value'], title='Category Distributions', sig_p_col='p_value'))
    html.append(table_html(trn, ['label', 'responder_selected', 'nonresponder_selected', 'test', 'p_value', 'interpretation'], title='Formal Training in GBV Handling (Q0010)', sig_p_col='p_value'))
    html.append(table_html(bar, ['label', 'responder_selected', 'nonresponder_selected', 'test', 'p_value', 'interpretation'], title='Barriers (Q0013)', sig_p_col='p_value'))
    html.append(table_html(conf, ['label', 'responder_mean', 'nonresponder_mean', 'test', 'p_value', 'interpretation'], title='Confidence Items (Q0014)', sig_p_col='p_value'))
    html.append(table_html(confo, ['label', 'responder_mean', 'nonresponder_mean', 'test', 'p_value', 'interpretation'], title='Overall Confidence'))
    html.append(table_html(know, ['label', 'responder_mean', 'nonresponder_mean', 'test', 'p_value', 'interpretation'], title='Knowledge Numeric Scores (Q0015-Q0017)', sig_p_col='p_value'))

    html.append('<h2>State Patterns (SAV labels)</h2>')
    html.append(table_html(s_top, ['state_name', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct'], title='States with Largest Absolute Completer Counts', pct_bar_cols={'completion_rate_pct'}))
    html.append(table_html(s_zero, ['state_name', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct'], title='States with No Matched Cases'))
    html.append(table_html(s_ext, ['metric', 'state_name', 'n_responder', 'n_nonresponder', 'total_n', 'completion_rate_pct'], title='Highest/Lowest Completion Rates (n>=10)', pct_bar_cols={'completion_rate_pct'}))
    html.append(table_html(s_cnt, ['metric', 'value'], title='State Coverage Summary'))

    html.append('<h2>Interpretation</h2>')
    html.append('<ul>' + ''.join(f'<li>{x}</li>' for x in lines) + '</ul>')
    html.append('</body></html>')

    out = BASE / 'FINAL_Analysis2_Responder362_vs_NonResponders453.html'
    out.write_text('\n'.join(html), encoding='utf-8')


def build_index_html():
    html = []
    html.append('<!doctype html><html><head><meta charset="utf-8"><title>Final Reports Index</title>')
    html.append(CSS)
    html.append('</head><body>')
    html.append('<h1>Pre-Post Final Reports</h1>')
    html.append('<div class="card-grid">')
    html.append('<div class="card"><div class="k">Analysis 1</div><div class="v"><a href="FINAL_Analysis1_Responder362_vs_AllNonResponders512.html">362 vs 512 (All non-responders)</a></div></div>')
    html.append('<div class="card"><div class="k">Analysis 2</div><div class="v"><a href="FINAL_Analysis2_Responder362_vs_NonResponders453.html">362 vs 453 (Old logic)</a></div></div>')
    html.append('</div>')
    html.append('<p class="small">If Word files fail to open, use these HTML files as primary reports.</p>')
    html.append('</body></html>')
    (BASE / 'FINAL_Reports_Index.html').write_text('\n'.join(html), encoding='utf-8')


def main():
    build_analysis1_html()
    build_analysis2_html()
    build_index_html()
    print('HTML reports generated.')


if __name__ == '__main__':
    main()
