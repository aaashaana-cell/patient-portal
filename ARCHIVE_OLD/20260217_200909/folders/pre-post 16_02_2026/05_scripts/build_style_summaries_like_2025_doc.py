#!/usr/bin/env python3
import csv
from pathlib import Path

BASE = Path('/Users/shanuakshah/Downloads/files (3)/pre-post 16_02_2026')
R512 = BASE / '02_results_362v512'
R453 = BASE / '03_results_362v453'
DATA = BASE / '04_datasets_mappings'
OUT = BASE / '00_final_reports'
PACK = BASE / '01_interpretation_pack'


def read_csv(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def read_txt(path):
    with open(path, encoding='utf-8') as f:
        return [x.strip() for x in f if x.strip()]


def p_num(p):
    p = (p or '').strip()
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


def sig(p):
    x = p_num(p)
    return x is not None and x < 0.05


def parse_npct(s):
    s = (s or '').strip()
    if '(' not in s:
        return None, None
    try:
        n = int(s.split('(')[0].strip())
        pct = float(s.split('(')[1].split(')')[0].replace('%', '').strip())
        return n, pct
    except Exception:
        return None, None


def esc(s):
    s = str(s)
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def table_html(rows, cols, title=None):
    out = []
    if title:
        out.append(f'<h3>{esc(title)}</h3>')
    if not rows:
        out.append('<p><em>No data.</em></p>')
        return '\n'.join(out)
    out.append('<table>')
    out.append('<thead><tr>' + ''.join(f'<th>{esc(c)}</th>' for c in cols) + '</tr></thead><tbody>')
    for r in rows:
        cls = ' class="sig"' if sig(r.get('p_value', '')) else ''
        out.append(f'<tr{cls}>' + ''.join(f'<td>{esc(r.get(c, ""))}</td>' for c in cols) + '</tr>')
    out.append('</tbody></table>')
    return '\n'.join(out)


def state_map():
    mp = {}
    for r in read_csv(DATA / 'state_code_mapping_full_from_sav.csv'):
        mp[str(r['state_code']).strip()] = r['state_name']
    return mp


def label_states(rows, code_col='state_code'):
    sm = state_map()
    out = []
    for r in rows:
        z = dict(r)
        z['state_name'] = sm.get(str(r.get(code_col, '')).strip(), z.get('state_name', r.get(code_col, '')))
        out.append(z)
    return out


def section_core(rdir, prefix, labeled_state_levels=False):
    age = read_csv(rdir / f'{prefix}_age_numeric_test.csv')[0]
    cat_tests = read_csv(rdir / f'{prefix}_categorical_tests.csv')
    cat_levels = read_csv(rdir / f'{prefix}_categorical_levels{("_labeled" if labeled_state_levels else "")}.csv')
    train = read_csv(rdir / f'{prefix}_training_checkbox_tests.csv')
    barrier = read_csv(rdir / f'{prefix}_barrier_checkbox_tests.csv')
    conf_items = read_csv(rdir / f'{prefix}_confidence_item_tests.csv')
    conf_overall = read_csv(rdir / f'{prefix}_confidence_overall_test.csv')[0]
    know = read_csv(rdir / f'{prefix}_knowledge_numeric_tests.csv')
    st_top = read_csv(rdir / f'{prefix}_state_top_completers{("_labeled" if labeled_state_levels else "")}.csv')
    st_zero = read_csv(rdir / f'{prefix}_state_no_matched_cases{("_labeled" if labeled_state_levels else "")}.csv')
    st_ext = read_csv(rdir / f'{prefix}_state_rate_extremes_n_ge_10{("_labeled" if labeled_state_levels else "")}.csv')
    st_cnt = read_csv(rdir / f'{prefix}_state_counts_summary.csv')

    if not labeled_state_levels:
        # add labels by mapping for 512 outputs
        st_top = label_states(st_top)
        st_zero = label_states(st_zero)
        st_ext = label_states(st_ext)
        for r in cat_levels:
            if r.get('variable') == 'q0007':
                r['level_label'] = state_map().get(str(r.get('level_code', '')).strip(), r.get('level_label', ''))

    return {
        'age': age,
        'cat_tests': cat_tests,
        'cat_levels': cat_levels,
        'train': train,
        'barrier': barrier,
        'conf_items': conf_items,
        'conf_overall': conf_overall,
        'know': know,
        'st_top': st_top,
        'st_zero': st_zero,
        'st_ext': st_ext,
        'st_cnt': st_cnt,
    }


def filter_levels(rows, var):
    return [r for r in rows if r.get('variable') == var]


def sig_rows(rows):
    return [r for r in rows if sig(r.get('p_value', ''))]


CSS = """
<style>
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; margin: 24px; color: #132238; background: #f7fafc; }
h1 { font-size: 28px; margin: 0 0 8px 0; }
h2 { font-size: 20px; margin: 26px 0 8px 0; }
h3 { font-size: 16px; margin: 16px 0 6px 0; }
p, li { line-height: 1.45; }
.small { font-size: 12px; color: #486581; }
.note { background: #fff8e1; border: 1px solid #f0d17a; border-radius: 10px; padding: 10px 12px; }
.cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin: 12px 0 16px 0; }
.card { background: #fff; border: 1px solid #d9e2ec; border-radius: 10px; padding: 10px 12px; }
.card .k { font-size: 12px; color: #486581; }
.card .v { font-size: 20px; font-weight: 700; margin-top: 4px; }
table { border-collapse: collapse; width: 100%; background: white; border: 1px solid #d9e2ec; font-size: 12px; margin-bottom: 10px; }
th, td { border: 1px solid #e4ebf2; padding: 6px 8px; vertical-align: top; }
th { background: #f0f4f8; text-align: left; }
tr.sig td { background: #fff7e6; }
</style>
"""


def build_doc(title, subtitle, prep_points, miss_points, core, summary_lines, out_name):
    html = []
    html.append('<!doctype html><html><head><meta charset="utf-8">')
    html.append(f'<title>{esc(title)}</title>')
    html.append(CSS)
    html.append('</head><body>')
    html.append(f'<h1>{esc(title)}</h1>')
    html.append(f'<p class="small">{esc(subtitle)}</p>')

    # quick cards
    age = core['age']
    cat_sig = sig_rows(core['cat_tests'])
    html.append('<div class="cards">')
    html.append(f"<div class='card'><div class='k'>Age p-value</div><div class='v'>{esc(age['p_value'])}</div></div>")
    html.append(f"<div class='card'><div class='k'>Significant core categorical variables</div><div class='v'>{len(cat_sig)}</div></div>")
    html.append(f"<div class='card'><div class='k'>Significant barrier items</div><div class='v'>{len(sig_rows(core['barrier']))}</div></div>")
    html.append(f"<div class='card'><div class='k'>Significant confidence items</div><div class='v'>{len(sig_rows(core['conf_items']))}</div></div>")
    html.append('</div>')

    html.append('<h2>Data preparation</h2><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in prep_points) + '</ul>')
    if miss_points:
        html.append('<h2>Missing-data profile</h2><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in miss_points) + '</ul>')

    html.append('<h2>Age</h2>')
    html.append(table_html([{
        'Group': 'Matched (Responder)',
        'n': age['responder_n'],
        'Mean age': age['responder_mean'],
        'SD': age['responder_sd'],
    },{
        'Group': 'Comparison Non-responder',
        'n': age['nonresponder_n'],
        'Mean age': age['nonresponder_mean'],
        'SD': age['nonresponder_sd'],
    }], ['Group','n','Mean age','SD']))
    html.append(f"<p><strong>Test:</strong> {esc(age['test'])}; <strong>p-value:</strong> {esc(age['p_value'])}. {esc(age['interpretation'])}</p>")

    html.append('<h2>Gender, education, experience, training programs, caseload, state, knowledge</h2>')
    html.append(table_html(core['cat_tests'], ['label','test','p_value','interpretation']))

    html.append('<h2>Detailed distributions</h2>')
    for var, label in [('q0006','Gender'),('q0008','Education'),('q0009','Years of experience'),('q0011','Post-joining training programs'),('q0012','GBV caseload'),('q0015','Knowledge'),('q0016','Resource awareness'),('q0017','Mental health awareness')]:
        rows = filter_levels(core['cat_levels'], var)
        html.append(table_html(rows, ['label','level_label','responder','nonresponder','p_value'], title=label))

    html.append('<h2>State patterns</h2>')
    html.append(table_html(core['st_top'], ['state_name','n_responder','n_nonresponder','total_n','completion_rate_pct'], title='States with largest absolute completer counts'))
    html.append(table_html(core['st_zero'], ['state_name','n_responder','n_nonresponder','total_n','completion_rate_pct'], title='States with no matched cases'))
    html.append(table_html(core['st_ext'], ['metric','state_name','n_responder','n_nonresponder','total_n','completion_rate_pct'], title='Highest and lowest completion rates (n>=10)'))
    html.append(table_html(core['st_cnt'], ['metric','value'], title='State count summary'))

    html.append('<h2>Formal training details (Q0010)</h2>')
    html.append(table_html(core['train'], ['label','responder_selected','nonresponder_selected','p_value','interpretation']))

    # append collapsed training if available
    any_train = read_csv(PACK / 'INTERPRETATION_PACK_06_AnyTraining_Collapsed.csv')
    row = next((r for r in any_train if ('512' in out_name and r['comparison']=='362_vs_512') or ('453' in out_name and r['comparison']=='362_vs_453')), None)
    if row:
        html.append(f"<p><strong>Collapsed any formal training:</strong> Matched {float(row['responder_any_training_pct']):.1f}% vs comparison {float(row['nonresponder_any_training_pct']):.1f}%, p={float(row['p_value']):.4f}.</p>")

    html.append('<h2>Barrier findings (Q0013)</h2>')
    html.append(table_html(core['barrier'], ['label','responder_selected','nonresponder_selected','p_value','interpretation']))

    # barrier count summary
    bcnt = read_csv(PACK / 'INTERPRETATION_PACK_05_BarrierCount_Summary.csv')
    brow = next((r for r in bcnt if ('512' in out_name and r['comparison']=='362_vs_512') or ('453' in out_name and r['comparison']=='362_vs_453')), None)
    if brow:
        html.append(f"<p><strong>Barrier count summary:</strong> Matched mean±SD = {float(brow['responder_mean']):.2f} ± {float(brow['responder_sd']):.2f}; comparison mean±SD = {float(brow['nonresponder_mean']):.2f} ± {float(brow['nonresponder_sd']):.2f}; Welch t-test p={float(brow['p_value']):.4f}.</p>")

    html.append('<h2>Confidence and knowledge</h2>')
    html.append(table_html(core['conf_items'], ['label','responder_mean','nonresponder_mean','p_value','interpretation'], title='Confidence item-level tests (Q0014)'))
    html.append(table_html([core['conf_overall']], ['label','responder_mean','nonresponder_mean','p_value','interpretation'], title='Overall confidence index'))
    html.append(table_html(core['know'], ['label','responder_mean','nonresponder_mean','p_value','interpretation'], title='Knowledge numeric scores'))

    html.append('<h2>Overall interpretation</h2><ul>' + ''.join(f'<li>{esc(x)}</li>' for x in summary_lines) + '</ul>')
    html.append('</body></html>')

    out_path = OUT / out_name
    out_path.write_text('\n'.join(html), encoding='utf-8')
    return out_path


def main():
    # analysis 1 style summary (362 vs 512)
    core512 = section_core(R512, 'rerun2026_analysis2_all512', labeled_state_levels=False)
    miss_lines = read_txt(R512 / 'rerun2026_analysis1_summary.txt')
    prep512 = [
        'Two groups compared: 362 matched responders vs 512 all non-responders from pre-assessment.',
        'Analysis includes demographics, training, barriers, confidence, knowledge and state patterns.',
        'State names mapped using SAV value labels.',
    ]
    out1 = build_doc(
        title='Narrative Summary (Style-Matched): 362 Responders vs 512 Non-Responders',
        subtitle='Version aligned to your 2025 narrative style, including both missingness and demographic analyses.',
        prep_points=prep512,
        miss_points=miss_lines,
        core=core512,
        summary_lines=read_txt(R512 / 'rerun2026_analysis2_all512_summary.txt'),
        out_name='SUMMARY_STYLE_Analysis1_362vs512.html'
    )

    # analysis 2 style summary (362 vs 453)
    core453 = section_core(R453, 'rerun2026_analysis2_oldlogic453', labeled_state_levels=True)
    prep453 = [
        'Two groups compared: 362 matched responders vs 453 non-responders (old logic: excluded rows with all three contact fields missing).',
        'Analysis includes demographics, training, barriers, confidence, knowledge and state patterns.',
        'State names mapped using SAV value labels.',
    ]
    out2 = build_doc(
        title='Narrative Summary (Style-Matched): 362 Responders vs 453 Non-Responders',
        subtitle='Version aligned to your 2025 narrative style and old non-responder definition.',
        prep_points=prep453,
        miss_points=[],
        core=core453,
        summary_lines=read_txt(R453 / 'rerun2026_analysis2_oldlogic453_summary.txt'),
        out_name='SUMMARY_STYLE_Analysis2_362vs453.html'
    )

    # quick links page
    idx = OUT / 'SUMMARY_STYLE_Index.html'
    idx.write_text(
        '\n'.join([
            '<!doctype html><html><head><meta charset="utf-8"><title>Style-Matched Summaries</title></head><body>',
            '<h1>Style-Matched Narrative Summaries</h1>',
            f'<p><a href="{out1.name}">Summary 1: 362 vs 512</a></p>',
            f'<p><a href="{out2.name}">Summary 2: 362 vs 453</a></p>',
            '</body></html>'
        ]), encoding='utf-8'
    )

    print('Created:', out1)
    print('Created:', out2)
    print('Created:', idx)


if __name__ == '__main__':
    main()
