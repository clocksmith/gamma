"""Paired B1 table setup plus N future answers at the observed mean cost."""

from argparse import ArgumentParser
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path

ARMS = ('ra_bare', 'kv_ctx', 'probe_bare')
RIVALS = ARMS[1:]
SCOPE = (
    'Measured full setup plus N times the observed paired arithmetic mean per answer, including KV restore. '
    'The range is an estimate for this observed mix, not a deployment guarantee. Null range means no positive query count pays back.'
)


def cost_interval(setup_gap, query_gap):
    """Positive integers N where setup_gap + N*query_gap <= 0; None means never."""
    intercept, slope = Fraction(setup_gap), Fraction(query_gap)
    if not slope:
        return {'first': 1, 'last': None} if intercept <= 0 else None
    crossing = -intercept / slope
    if slope < 0:
        return {'first': max(1, -(-crossing.numerator // crossing.denominator)), 'last': None}
    last = crossing.numerator // crossing.denominator
    return {'first': 1, 'last': last} if last >= 1 else None


def checked_ms(v):
    if (
        isinstance(v, bool)
        or not isinstance(v, (int, Decimal))
        or (isinstance(v, Decimal) and not v.is_finite())
        or v < 0
    ):
        raise ValueError(f'Invalid measured milliseconds {v!r}')
    return Fraction(v)


def comparison(setup, means, rival, observed=None):
    delta, slope = setup['ra_bare'] - setup[rival], means['ra_bare'] - means[rival]
    win = cost_interval(delta, slope)
    other = cost_interval(-delta, -slope)
    if not slope:
        ties = {'first': 1, 'last': None} if not delta else None
    else:
        n = -delta / slope
        ties = {'first': int(n), 'last': int(n)} if n.denominator == 1 and n >= 1 else None
    result = {
        'adapterAtLeastAsFastAtQueryCounts': win,
        'otherAtLeastAsFastAtQueryCounts': other,
        'equalTimeAtQueryCounts': ties,
        'otherSetupMs': float(setup[rival]),
        'otherMeanMsPerAnswer': float(means[rival]),
        'adapterMinusOtherSetupMs': float(delta),
        'adapterMinusOtherMeanMsPerAnswer': float(slope),
    }
    if observed is not None:
        result['adapterMinusOtherAtObservedCountMs'] = float(delta + observed * slope)
    return result


def stats(setup, queries, ids):
    means = {a: sum(queries[i][a] for i in ids) / len(ids) for a in ARMS}
    out = {
        'count': len(ids),
        'adapterSetupMs': float(setup['ra_bare']),
        'adapterMeanMsPerAnswer': float(means['ra_bare']),
        'comparisons': {a: comparison(setup, means, a, len(ids)) for a in RIVALS},
    }
    return out, (setup, means, len(ids))


def cohort(tables):
    """One setup and N queries on each represented table; weight each table equally."""
    setup, means = {}, {}
    for a in ARMS:
        setup[a] = sum(s[a] for s, _, _ in tables) / len(tables)
        means[a] = sum(m[a] for _, m, _ in tables) / len(tables)
    out = {
        'tables': len(tables),
        'observedQuestions': sum(n for _, _, n in tables),
        'adapterMeanSetupMsPerTable': float(setup['ra_bare']),
        'adapterMeanMsPerAnswer': float(means['ra_bare']),
        'comparisons': {},
    }
    for a in RIVALS:
        counts = Counter(
            dict.fromkeys(
                ('noPayback', 'onlyThroughFiniteCount', 'allPositiveCounts', 'fromThresholdOnward'), 0
            )
        )
        for s, m, _ in tables:
            w = cost_interval(s['ra_bare'] - s[a], m['ra_bare'] - m[a])
            if w is None:
                counts['noPayback'] += 1
            elif w['last'] is not None:
                counts['onlyThroughFiniteCount'] += 1
            elif w['first'] == 1:
                counts['allPositiveCounts'] += 1
            else:
                counts['fromThresholdOnward'] += 1
        out['comparisons'][a] = {**comparison(setup, means, a), 'perTableCounts': dict(counts)}
    return out


def report(paths, *, token_lengths=None, layout=None, overlap=None):
    """layout maps each receipt basename to its expected numbered tables and task IDs."""
    by_table = {}
    cohorts = defaultdict(list)
    seen_tasks = set()
    for path in paths:
        receipt = json.loads(path.read_text(), parse_float=Decimal)
        family = (receipt.get('model'), receipt.get('split'), receipt.get('seed'))
        queries = defaultdict(dict)
        labels = {}
        for row in receipt['rows']:
            a = row['arm']
            if a not in ARMS:
                continue
            t, q = row['specialty_id'], row['task_id']
            if type(q) is not int or q < 0:
                raise ValueError(f'Invalid integer task ID {q!r}')
            methods = queries[t].setdefault(q, {})
            if a in methods:
                raise ValueError(f'Duplicate arm {a} for integer task {q} in table {t}')
            methods[a] = checked_ms(row['total_ms'])
            label = (t, row['expected'], row['multi_token'], row.get('group'))
            if type(label[2]) is not bool:
                raise ValueError(f'Missing code-shape flag at task {q}')
            if labels.setdefault(q, label) != label:
                raise ValueError(f'Unpaired table or target for task {q}')
        if 'task_count' in receipt and len(labels) != receipt['task_count']:
            raise ValueError('Missing whole paired question(s) in ' + path.name)
        for q in labels:
            if (*family, q) in seen_tasks:
                raise ValueError(f'Duplicate integer task ID {q} across receipts')
            seen_tasks.add((*family, q))
        compiled = {}
        for t in receipt['specialties_compiled']:
            name = t['specialty_id']
            if name in compiled or name in by_table:
                raise ValueError('Repeated table ' + name)
            compiled[name] = t
        if not compiled or set(compiled) != set(queries):
            raise ValueError('Orphan or missing paired table in ' + path.name)
        if layout is not None and set(compiled) != set(layout[path.name]):
            raise ValueError('Receipt does not cover its full table range: ' + path.name)
        for name, t in compiled.items():
            pairs = queries[name]
            if any(set(v) != set(ARMS) for v in pairs.values()):
                raise ValueError('Unpaired measurements in ' + name)
            ids = sorted(pairs)
            if layout is not None:
                index, expected_ids = layout[path.name][name]
                if set(ids) != expected_ids:
                    raise ValueError('Incorrect IDs or missing whole question in ' + name)
            samples = {labels[q][2] for q in ids}
            if len(samples) != 1:
                raise ValueError('Mixed code-shape flag within table ' + name)
            shape = 'twoPartCode' if samples.pop() else 'wordCode'
            setup = {
                'ra_bare': checked_ms(t['readout_adapter_compile_ms']),
                'kv_ctx': checked_ms(t['kv_snapshot']['kv_build_ms']),
                'probe_bare': checked_ms(t['classifier_compile_ms']),
            }
            entry, raw = stats(setup, pairs, ids)
            by_table[name] = entry
            entry['codeShape'] = shape
            cohorts['allTables'].append(raw)
            cohorts[shape].append(raw)
            if overlap is not None:
                if layout is None:
                    raise ValueError('Timing overlap marking requires table indices')
                flagged = overlap[0] <= index < overlap[1]
                entry['reportedBuildOverlapPossible'] = flagged
                cohort_name = 'reportedOverlapRange' if flagged else 'outsideReportedOverlapRange'
                cohorts[cohort_name].append(raw)
                cohorts[cohort_name + '.' + shape].append(raw)
            if token_lengths is None:
                continue
            strata = defaultdict(list)
            for q in ids:
                code = labels[q][1]
                length = token_lengths[code]
                kind = (
                    'twoPartCode'
                    if shape == 'twoPartCode'
                    else ('singleTokenWord' if length == 1 else 'multiTokenWord')
                )
                strata[(kind, length)].append(q)
            entry['byTargetTokenLength'] = {}
            for (kind, length), qids in sorted(strata.items()):
                key = f'{kind}.{length}tokens'
                s, subgroup = stats(setup, pairs, qids)
                entry['byTargetTokenLength'][key] = s
                cohorts['target.' + key].append(subgroup)
                if overlap is not None:
                    cohorts[cohort_name + '.target.' + key].append(subgroup)
    if not by_table:
        raise ValueError('No measured tables')
    return {
        'scope': SCOPE,
        'tables': by_table,
        'cohorts': {k: cohort(v) for k, v in sorted(cohorts.items())},
        'cohortMeaning': 'Estimated mean total time for one table drawn uniformly from this cohort and N answers on that table. Target-length comparisons charge full setup even for a restricted question mix. Rows from the reported overlap always remain in the primary cohort.',
    }


if __name__ == '__main__':
    ap = ArgumentParser(description=__doc__)
    ap.add_argument('receipts', nargs='+', type=Path)
    print(json.dumps(report(ap.parse_args().receipts), indent=2, allow_nan=False))
