#!/usr/bin/env python3
import csv
import re
from collections import defaultdict, Counter
from pathlib import Path

OUT_DIR = Path('/Users/shanuakshah/Downloads/files (3)/pre-post 16_02_2026')
PRE_PATH = OUT_DIR / 'pre_from_sav.csv'
COL_PATH = OUT_DIR / 'colleague_362_matched.csv'


def clean(v):
    if v is None:
        return ''
    v = str(v).strip()
    if v.upper() == 'NA':
        return ''
    return v


def norm_id(v):
    return re.sub(r'[^A-Z0-9]+', '', clean(v).upper())


def norm_name(v):
    s = clean(v).lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s)
    return ' '.join(s.split())


def norm_email(v):
    return clean(v).lower().replace(' ', '')


def valid_email(v):
    return bool(re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', v or ''))


ANALYSIS_COLS = [
    'q0002', 'q0003', 'q0004',
    'q0005', 'q0006', 'q0006_other', 'q0007', 'q0008', 'q0008_other', 'q0009',
    'q0011', 'q0012', 'q0015', 'q0016', 'q0017',
]
ANALYSIS_COLS += [f'q0010_{i:04d}' for i in range(1, 6)] + ['q0010_other']
ANALYSIS_COLS += [f'q0013_{i:04d}' for i in range(1, 13)] + ['q0013_other']
ANALYSIS_COLS += [f'q0014_{i:04d}' for i in range(1, 17)]

CONTENT_COLS = [
    c for c in ANALYSIS_COLS if c not in ('q0002', 'q0003', 'q0004')
]

COL_TO_PRE = {
    'q0002': 'q0002_initials',
    'q0003': 'q0003_name',
    'q0004': 'q0004_email',
    'q0005': 'q0005_age',
    'q0006': 'q0006_gender',
    'q0006_other': 'q0006_other',
    'q0007': 'q0007_state',
    'q0008': 'q0008_education',
    'q0008_other': 'q0008_other',
    'q0009': 'q0009_yearsofexperience',
    'q0011': 'q0011_pre_trainingprog',
    'q0012': 'q0012_pre_nowomenosc',
    'q0015': 'q0015_pre_knowledgegbv',
    'q0016': 'q0016_pre_awareness_localresources',
    'q0017': 'q0017_pre_awareness_mentalhealth_gbv',
    'q0010_0001': 'q0010_0001_pre_noformaltraining',
    'q0010_0002': 'q0010_0002_pre_lecturs',
    'q0010_0003': 'q0010_0003_pre_skillworkshop',
    'q0010_0004': 'q0010_0004_pre_certcourse',
    'q0010_0005': 'q0010_0005_pre_degree',
    'q0010_other': 'q0010_other',
    'q0013_0001': 'q0013_0001_prebarrier_time',
    'q0013_0002': 'q0013_0002_prebarrier_DV',
    'q0013_0003': 'q0013_0003_prebarrier_IPV',
    'q0013_0004': 'q0013_0004_prebarrier_SV',
    'q0013_0005': 'q0013_0005_prebarrier_offend',
    'q0013_0006': 'q0013_0006_pre_privacy',
    'q0013_0007': 'q0013_0007_prebarrier_helpless',
    'q0013_0008': 'q0013_0008_prebarrier_resources',
    'q0013_0009': 'q0013_0009_pre_chnagethesituation',
    'q0013_0010': 'q0013_0010_pre_legalissues',
    'q0013_0011': 'q0013_0011_pre_perpetrator_sessions',
    'q0013_0012': 'q0013_0012_pre_other',
    'q0013_other': 'q0013_other',
}
for i in range(1, 17):
    COL_TO_PRE[f'q0014_{i:04d}'] = f'Qus14_pre{i}'

MATCH_COLS = [
    'q0002', 'q0003', 'q0004',
    'q0005', 'q0006', 'q0007', 'q0008', 'q0009',
    'q0011', 'q0012', 'q0015', 'q0016', 'q0017',
]
MATCH_COLS += [f'q0010_{i:04d}' for i in range(1, 6)] + ['q0010_other']
MATCH_COLS += [f'q0013_{i:04d}' for i in range(1, 13)]
MATCH_COLS += [f'q0014_{i:04d}' for i in range(1, 17)]


def read_csv_dict(path, encoding):
    with open(path, newline='', encoding=encoding, errors='replace') as f:
        return list(csv.DictReader(f))


def prep_pre(rows):
    out = []
    for i, r in enumerate(rows):
        z = {'pre_row_index': i}
        for c in ANALYSIS_COLS:
            z[c] = clean(r.get(c, ''))
        z['_id_norm'] = norm_id(z.get('q0002', ''))
        z['_name_norm'] = norm_name(z.get('q0003', ''))
        z['_email_norm'] = norm_email(z.get('q0004', ''))
        z['_content_score'] = sum(1 for c in CONTENT_COLS if clean(z.get(c, '')))
        z['_analysis_score'] = sum(1 for c in ANALYSIS_COLS if c not in ('q0002', 'q0003', 'q0004') and clean(z.get(c, '')))
        out.append(z)
    return out


def prep_col(rows):
    out = []
    for i, r in enumerate(rows):
        z = {'col_row_index': i}
        for c in ANALYSIS_COLS:
            src = COL_TO_PRE.get(c, '')
            z[c] = clean(r.get(src, ''))
        z['_id_norm'] = norm_id(z.get('q0002', ''))
        z['_name_norm'] = norm_name(z.get('q0003', ''))
        z['_email_norm'] = norm_email(z.get('q0004', ''))
        out.append(z)
    return out


def build_index(pre_rows):
    idx_signature = defaultdict(list)
    idx_triple = defaultdict(list)
    idx_email = defaultdict(list)
    idx_id_name = defaultdict(list)
    idx_id = defaultdict(list)
    idx_name = defaultdict(list)

    for r in pre_rows:
        i = r['pre_row_index']
        sig = tuple(clean(r.get(c, '')) for c in MATCH_COLS)
        idx_signature[sig].append(i)

        triple = (r['_id_norm'], r['_name_norm'], r['_email_norm'])
        idx_triple[triple].append(i)

        if r['_email_norm']:
            idx_email[r['_email_norm']].append(i)
        if r['_id_norm'] and r['_name_norm']:
            idx_id_name[(r['_id_norm'], r['_name_norm'])].append(i)
        if r['_id_norm']:
            idx_id[r['_id_norm']].append(i)
        if r['_name_norm']:
            idx_name[r['_name_norm']].append(i)

    return {
        'signature': idx_signature,
        'triple': idx_triple,
        'email': idx_email,
        'id_name': idx_id_name,
        'id': idx_id,
        'name': idx_name,
    }


def choose_best(cands, pre_by_idx):
    if not cands:
        return None
    cands = sorted(cands, key=lambda i: (-pre_by_idx[i]['_analysis_score'], i))
    return cands[0]


def canonical_key(row):
    eid = row['_id_norm']
    nm = row['_name_norm']
    em = row['_email_norm']
    if em and valid_email(em):
        return f'email|{em}'
    if nm and eid:
        return f'idname|{eid}|{nm}'
    if nm:
        return f'name|{nm}'
    if eid:
        return f'id|{eid}'
    if em:
        return f'email_raw|{em}'
    return f'row|{row["pre_row_index"]}'


def write_csv(path, rows, columns):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, '') for c in columns})


def main():
    pre_raw = read_csv_dict(PRE_PATH, 'utf-8-sig')
    col_raw = read_csv_dict(COL_PATH, 'latin1')

    pre = prep_pre(pre_raw)
    responders = prep_col(col_raw)

    pre_by_idx = {r['pre_row_index']: r for r in pre}
    idx = build_index(pre)

    method_counts = Counter()
    matched_links = []

    for r in responders:
        hit = None
        method = 'unmatched'

        sig = tuple(clean(r.get(c, '')) for c in MATCH_COLS)
        cands = idx['signature'].get(sig, [])
        if cands:
            hit = choose_best(cands, pre_by_idx)
            method = 'signature'

        if hit is None:
            triple = (r['_id_norm'], r['_name_norm'], r['_email_norm'])
            cands = idx['triple'].get(triple, [])
            if cands:
                hit = choose_best(cands, pre_by_idx)
                method = 'triple'

        if hit is None and r['_email_norm']:
            cands = idx['email'].get(r['_email_norm'], [])
            if cands:
                hit = choose_best(cands, pre_by_idx)
                method = 'email'

        if hit is None and r['_id_norm'] and r['_name_norm']:
            cands = idx['id_name'].get((r['_id_norm'], r['_name_norm']), [])
            if cands:
                hit = choose_best(cands, pre_by_idx)
                method = 'id_name'

        if hit is None and r['_id_norm']:
            cands = idx['id'].get(r['_id_norm'], [])
            if cands:
                hit = choose_best(cands, pre_by_idx)
                method = 'id'

        if hit is None and r['_name_norm']:
            cands = idx['name'].get(r['_name_norm'], [])
            if cands:
                hit = choose_best(cands, pre_by_idx)
                method = 'name'

        if hit is None and r['_id_norm']:
            pref = [
                pr['pre_row_index'] for pr in pre
                if pr['_id_norm'] and (pr['_id_norm'].startswith(r['_id_norm']) or r['_id_norm'].startswith(pr['_id_norm']))
            ]
            if pref:
                hit = choose_best(pref, pre_by_idx)
                method = 'id_prefix'

        method_counts[method] += 1
        matched_links.append({
            'col_row_index': r['col_row_index'],
            'match_method': method,
            'matched_pre_row_index': '' if hit is None else hit,
            'id': r.get('q0002', ''),
            'name': r.get('q0003', ''),
            'email': r.get('q0004', ''),
        })

    matched_pre_unique = sorted({m['matched_pre_row_index'] for m in matched_links if m['matched_pre_row_index'] != ''})
    matched_pre_set = set(matched_pre_unique)

    nonresp_all = [r for r in pre if r['pre_row_index'] not in matched_pre_set]

    best_by_key = {}
    for r in nonresp_all:
        k = canonical_key(r)
        if k not in best_by_key:
            best_by_key[k] = r
            continue
        old = best_by_key[k]
        if (r['_content_score'], -r['pre_row_index']) > (old['_content_score'], -old['pre_row_index']):
            best_by_key[k] = r
    nonresp_dedup = list(best_by_key.values())
    nonresp_clean = [r for r in nonresp_dedup if r['_content_score'] > 0]

    out_cols = ['group', 'row_source_index'] + ANALYSIS_COLS

    responders_out = []
    for r in responders:
        z = {c: r.get(c, '') for c in ANALYSIS_COLS}
        z['group'] = 'Responder_362'
        z['row_source_index'] = r['col_row_index']
        responders_out.append(z)

    nonresp_all_out = []
    for r in nonresp_all:
        z = {c: r.get(c, '') for c in ANALYSIS_COLS}
        z['group'] = 'NonResponder_All'
        z['row_source_index'] = r['pre_row_index']
        nonresp_all_out.append(z)

    nonresp_clean_out = []
    for r in nonresp_clean:
        z = {c: r.get(c, '') for c in ANALYSIS_COLS}
        z['group'] = 'NonResponder_Clean'
        z['row_source_index'] = r['pre_row_index']
        nonresp_clean_out.append(z)

    write_csv(OUT_DIR / 'rerun2026_responder_362_standardized.csv', responders_out, out_cols)
    write_csv(OUT_DIR / 'rerun2026_nonresponder_all_standardized.csv', nonresp_all_out, out_cols)
    write_csv(OUT_DIR / 'rerun2026_nonresponder_clean_standardized.csv', nonresp_clean_out, out_cols)

    link_cols = ['col_row_index', 'match_method', 'matched_pre_row_index', 'id', 'name', 'email']
    write_csv(OUT_DIR / 'rerun2026_colleague_to_pre_matching_audit.csv', matched_links, link_cols)

    summary_lines = [
        f'pre_total_rows,{len(pre)}',
        f'colleague_responder_rows,{len(responders)}',
        f'colleague_rows_with_pre_hit,{sum(1 for m in matched_links if m["matched_pre_row_index"] != "")}',
        f'matched_pre_unique_rows,{len(matched_pre_unique)}',
        f'nonresponders_all_rows,{len(nonresp_all)}',
        f'nonresponders_dedup_rows,{len(nonresp_dedup)}',
        f'nonresponders_clean_rows,{len(nonresp_clean)}',
    ]
    for k, v in sorted(method_counts.items()):
        summary_lines.append(f'match_method_{k},{v}')

    (OUT_DIR / 'rerun2026_set_construction_summary.csv').write_text('\n'.join(summary_lines) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
