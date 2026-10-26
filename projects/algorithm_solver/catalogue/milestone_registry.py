"""Validate/report milestone metadata only. Never loads sources, cases or models."""
from __future__ import annotations
import argparse
import json
import math
import hashlib
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
REGISTRY = HERE / 'roadmap-v1.json'
VIEW = HERE / 'MILESTONES.md'
STATUSES = {'not_qualified', 'failed', 'unmet', 'unmeasured', 'ungated', 'passed'}
VERIFICATION = {'owner_reported_unverified', 'locally_verified_metadata', 'committed_aggregate_read', 'independently_qualified'}

def gate_digest(gate):
    return hashlib.sha256(json.dumps(gate,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def valid_date(value):
    try:
        datetime.fromisoformat(value.replace("Z","+00:00"))
        return True
    except (ValueError, TypeError, AttributeError):
        return False

def validate(data):
    """Raise ValueError on inconsistent reporting; never certify a scientific gate."""
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    require(data.get('schema') == 'gamma.milestone-registry.v2', 'unsupported registry schema')
    rows = data.get('milestones', [])
    require(isinstance(rows, list) and rows, 'milestones required')
    ids = [r['id'] for r in rows]
    require(len(set(ids)) == len(ids), 'duplicate milestone ID')
    expected={f'{t}{i}' for t,n in [('D',4),('A',6),('H',3),('X',2)] for i in range(1,n+1)}
    require(set(ids)==expected, 'canonical milestone population changed')
    tracks = data['tracks']
    aliases = set(ids)
    evidence = data.get('evidence', [])
    eids = [e['id'] for e in evidence]
    require(len(set(eids)) == len(eids), 'duplicate evidence ID')
    by_eid = {e['id']: e for e in evidence}
    for e in evidence:
        require(e['verification'] in VERIFICATION, 'unknown evidence verification')
        require(bool(e.get('source')) and bool(e.get('scope')), 'evidence needs source and scope')
        require('observed_at' in e and valid_date(e.get('recorded_at')), 'valid evidence dates required; unknown observed_at is null')
        require(e['observed_at'] is None or valid_date(e['observed_at']), 'invalid observation date')
        digest = e.get('source_sha256')
        require(digest is None or (len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)), 'invalid source SHA256')
        names = set()
        for m in e.get('metrics', []):
            require(m['name'] not in names, 'duplicate metric name')
            names.add(m['name'])
            require('completion' not in m['name'].lower(), 'completion percentages forbidden')
            value = m['value']
            require(type(value) in (int, float) and math.isfinite(value) and value >= 0, 'invalid metric value')
            require(bool(m.get('unit')), 'metric unit required')
            if 'denominator' in m:
                den = m['denominator']
                require(type(den) in (int,float) and math.isfinite(den) and den > 0 and value <= den, 'invalid ratio denominator/numerator')
            if m['unit'] == 'percent':
                require(value <= 100, 'invalid percentage')
    for row in rows:
        require(row['track'] in tracks and row['id'].startswith(row['track']), 'invalid track')
        require(row['status'] in STATUSES, 'unknown milestone status')
        require(bool(row.get('authority')) and bool(row.get('goal_ids')), 'authority and goal tags required')
        require(row.get('approval_status') in {'agreed','proposed','hypothetical','goal_approved_gate_undefined'}, 'invalid approval status')
        for alias in row.get('aliases', []):
            require(alias not in aliases, 'ambiguous alias')
            aliases.add(alias)
        expected_alias = ('R'+row['id'][1:]) if row['track']=='D' else ('M'+row['id'][1:]) if row['track']=='A' else None
        require(expected_alias is None or expected_alias in row['aliases'], 'historical alias missing')
        g = row['gate']
        require(row.get('gate_sha256')==gate_digest(g), 'gate changed without authorized version/hash update')
        require(g['readiness'] in {'defined','undefined','needs_thresholds'}, 'unknown gate readiness')
        require(isinstance(g['all_of'],list) and g['all_of'] and all(isinstance(c,str) and c.strip() for c in g['all_of']), 'full gate clauses required')
        require(all(d in ids and d != row['id'] for d in g['requires']), 'invalid gate dependency')
        require(all(e in by_eid for e in row['evidence_ids']), 'missing evidence reference')
        if row['status'] == 'failed':
            require(g['readiness'] == 'defined' and row['evidence_ids'], 'failure requires defined gate and outcome evidence')
        if row['status'] == 'passed':
            require(g['readiness'] == 'defined', 'undefined gate cannot pass')
            require(row['approval_status']=='agreed', 'proposed/hypothetical gate needs approval before qualification')
            qualification = row.get('qualification')
            require(isinstance(qualification,dict), 'pass requires explicit full-gate qualification')
            refs = qualification.get('evidence_ids', [])
            require(refs and all(e in row['evidence_ids'] and by_eid[e]['verification'] == 'independently_qualified' for e in refs), 'reported or metadata evidence cannot qualify a pass')
            require(qualification.get('all_clauses_satisfied') is True and bool(qualification.get('review_authority')), 'pass requires all clauses and review authority')
            require(qualification.get('gate_sha256')==row['gate_sha256'], 'qualification is bound to a different gate')
            require(valid_date(qualification.get('verified_at')), 'qualification date required')
            coverage=qualification.get('clause_evidence', {})
            require(set(coverage)=={str(i) for i in range(len(g['all_of']))}, 'every gate clause requires evidence')
            require(all(isinstance(v,list) and v and all(ref in refs for ref in v) for v in coverage.values()), 'invalid clause evidence')
            require(all(by_eid[ref].get('source_sha256') and by_eid[ref].get('observed_at') for ref in refs), 'qualification requires immutable receipt identity and observation date')
    graph = {r['id']:r['gate']['requires'] for r in rows}
    def visit(node, trail):
        require(node not in trail, 'cyclic gate dependency')
        for child in graph[node]:
            visit(child, trail | {node})
    for node in graph:
        visit(node,set())
    for row in rows:
        if row['status'] == 'passed':
            require(all(next(r for r in rows if r['id']==d)['status']=='passed' for d in graph[row['id']]), 'required milestone not passed')
    return data

def resolve(data, identifier):
    for row in data['milestones']:
        if identifier == row['id'] or identifier in row['aliases']:
            return row
    raise KeyError(identifier)

def render(data):
    validate(data)
    out = ['# Gamma milestone registry', '', '<!-- GENERATED from roadmap-v1.json by milestone_registry.py; do not edit. -->', '',
           'One current registry: [roadmap-v1.json](roadmap-v1.json). Goals are tags, not completion units. Measured ratios are not percentages of work complete. Historical contracts and immutable receipts retain their original authority.', '',
           'This report is metadata, not scientific qualification or permission to execute, publish, train or open protected data.', '',
           '## Track status', '', '| Track | Demonstrated passes | Gates defined | Authority caveat |', '|---|---:|---:|---|']
    for track,name in data['tracks'].items():
        rows=[r for r in data['milestones'] if r['track']==track]
        out.append(f"| {track}: {name} | {sum(r['status']=='passed' for r in rows)}/{len(rows)} | {sum(r['gate']['readiness']=='defined' for r in rows)}/{len(rows)} | " + ('Includes proposed/hypothetical targets; not all accepted delivery promises.' if track=='A' else 'Undefined gates are not failures.' if track in 'HX' else 'D3 still needs quantitative thresholds.') + ' |')
    for row in data['milestones']:
        out += ['', f"## {row['id']}: {row['name']}", '', f"Aliases: {', '.join(row['aliases']) or 'none'}; goal tags: {', '.join(row['goal_ids'])}.", f"Authority: {row['authority']} ({row['approval_status']}). Status: **{row['status']}**. Gate readiness: **{row['gate']['readiness']}**.", '', '### Full acceptance gate (all clauses)', '']
        out += ['- '+c.replace('\n','\n  ') for c in row['gate']['all_of']]
        if row['gate']['requires']:
            out += ['- Also requires the complete gates of: '+', '.join(row['gate']['requires'])+'.']
        out += ['', 'Evidence: '+(', '.join('['+eid+'](#'+eid+')' for eid in row['evidence_ids']) or 'No qualifying outcome recorded; this is not a measured zero success rate.')]
    out += ['', '## Evidence snapshots', '']
    for e in data['evidence']:
        out += [f"### {e['id']}", '', f"Verification: **{e['verification']}**. Observed: {e['observed_at'] or 'unknown'}; recorded: {e['recorded_at']}.", '', f"Source: `{e['source']}`.", '', e['scope'], '']
        if e.get('source_commit'):
            out += ['Source commit: `'+e['source_commit']+'`.', '']
        if e.get('source_sha256'):
            out += ['Source SHA-256: `'+e['source_sha256']+'`.', '']
        for m in e['metrics']:
            val=str(m['value'])
            if 'denominator' in m:
                val+=f"/{m['denominator']} ({100*m['value']/m['denominator']:.3f}% measured ratio)"
            out.append(f"- {m['name']}: {val} {m['unit']}.")
        out.append('')
    out += ['## Maintenance', '', 'Edit the existing JSON registry, then run `python3 projects/algorithm_solver/catalogue/milestone_registry.py --write`.', 'Check metadata and generated-view freshness with `python3 projects/algorithm_solver/catalogue/milestone_registry.py --check`.', 'Run focused tests with `python3 -m unittest discover -s projects/algorithm_solver/catalogue -p test_milestone_registry.py`.', 'Never overwrite historical receipts or turn a newer report into independently verified evidence without the corresponding scoped verification.', 'Historical definitions: [R1-R4](ROADMAP-v1.md), [M1-M6](../literals/MILESTONES.md), [goal taxonomy](../contracts/algorithm_solver_goals_v2.json).', '']
    return '\n'.join(line.rstrip() for block in out for line in block.split('\n'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    args=parser.parse_args()
    output=render(json.loads(REGISTRY.read_text()))
    if args.write:
        VIEW.write_text(output)
    elif not VIEW.exists() or VIEW.read_text()!=output:
        parser.exit(1,'Generated milestone view is stale; run --write.\n')
    print('Milestone metadata and generated view valid; scientific qualification not performed.')
if __name__=='__main__':
    main()
