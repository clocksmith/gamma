"""Expressibility report for a BITS step 1 target build (aggregates and UIDs only).

  python expressibility.py <build dir> <teacher outputs jsonl> <out json>

Representation failures: the teacher's explicit abstentions (grouped by the
stated reason) and reviewer-blocked rows. Construction failures: proposals the
teacher wrote that failed compilation or a qualification stage. For each
qualified program: operations, control flow, data structures and effects used.
"""
import collections, glob, json, re, sys
from pathlib import Path

build, teacher_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
teacher = {json.loads(l)['uid']: json.loads(l) for l in teacher_path.read_text().splitlines()}
REASONS = [('string_or_text', r'\bstr(ing)?s?\b|character|text|char\b'), ('tree_or_linked_list', r'tree|linked|listnode|node'),
           ('division_or_modulo', r'divis|modul|\bmod\b|remainder|floor|integer div|//'),
           ('indexing_or_random_access', r'index|random access|subscript|position'),
           ('float_or_real', r'float|real|decimal|double|fraction'), ('nested_or_2d_list', r'2d|matrix|grid|nested|list of lists'),
           ('sorting_or_ordering', r'sort'), ('bitwise', r'bit|xor|shift'), ('min_max', r'\bmin\b|\bmax\b|minimum|maximum')]


def category(text):
    text = text.lower()
    return [name for name, pattern in REASONS if re.search(pattern, text)] or ['other']


def walk(node, acc):
    if isinstance(node, dict):
        if 'op' in node:
            acc[node['op']] += 1
            if node['op'] == 'call':
                acc['effect:' + node['operator']] += 1
        for value in node.values():
            walk(value, acc)
    elif isinstance(node, list):
        for value in node:
            walk(value, acc)
    return acc


rows, abstentions, stage_failures, blocked = {}, collections.Counter(), collections.Counter(), {}
for path in sorted(glob.glob(str(build / 'attempts/*-receipt.json'))):
    receipt = json.loads(Path(path).read_text())
    uid = receipt['uid']
    if receipt.get('reason') == 'blocked':
        blocked[uid] = receipt.get('stage')
        rows[uid] = 'blocked:' + str(receipt.get('stage'))
        continue
    proposals = (teacher.get(uid) or {}).get('proposals') or []
    records = receipt.get('proposals', [])
    if any(r.get('reason') == 'qualified' for r in records):
        rows[uid] = 'qualified'
        continue
    abstain = [p for p in proposals if p.get('variant') == 'abstain']
    if abstain:
        reasons = (abstain[0].get('requirements') or {}).get('unsupported_requirements') or ['']
        for cat in category(' '.join(map(str, reasons))):
            abstentions[cat] += 1
        rows[uid] = 'teacher_abstained'
        continue
    stage = records[-1].get('stage') if records else 'none'
    stage_failures[stage] += 1
    rows[uid] = 'rejected_at:' + str(stage)

features, per_program = collections.Counter(), []
for line in (build / 'pairs.jsonl').read_text().splitlines():
    pair = json.loads(line)
    used = walk(pair['target']['program'], collections.Counter())
    types = json.dumps([pair['target']['program']['inputs'], pair['target']['program']['output_type']])
    kinds = sorted({k.split(':')[0] if k.startswith('effect:') else k for k in used})
    for k in set(used):
        features[k] += 1
    per_program.append({'uid': pair['uid'], 'features': sorted(used), 'uses_tuple': 'tuple' in types,
                        'statements': sum(used[k] for k in ('let', 'var', 'set', 'for', 'if', 'call'))})

report = {'schema': 'algsolve.bits-step1-expressibility.v1', 'build_summary': json.loads((build / 'summary.json').read_text())['counts'],
          'outcomes': dict(collections.Counter(v.split(':')[0] if not v.startswith('rejected_at') else v for v in rows.values())),
          'representation_failures': {'teacher_abstentions_by_stated_reason': dict(abstentions), 'reviewer_blocked': blocked},
          'construction_failures_by_stage': dict(stage_failures),
          'qualified_program_features': dict(features.most_common()),
          'qualified_programs': per_program, 'row_outcomes': rows,
          'note': 'Abstention categories are keyword groupings of the teacher\'s stated reasons (a reason can fall in several). '
                  'Construction failures are proposals the teacher did not abstain on that failed compilation or a qualification stage.'}
out.write_text(json.dumps(report, indent=1, sort_keys=True))
print(json.dumps({k: report[k] for k in ('outcomes', 'representation_failures', 'construction_failures_by_stage')}, indent=1))
print('features', dict(features.most_common(25)))
