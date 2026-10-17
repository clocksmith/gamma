"""Index-only structural mining. Outputs candidates, never a verified vocabulary.

Reserve fresh confirmation families before reading solution ASTs. No generated
code, model calls, downloads, hidden tests, or changes to vocabulary v1.
"""
from __future__ import annotations
import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from .. import splits
from ..records import LANE_ROOT


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def normalized(node):
    """Structural clustering only; matching hashes do not establish equivalence.

    Keep constants, attribute names and unbound globals. Canonicalize arguments
    and stored names, removing docstrings. Nested scope semantics still need
    inspection and explicit contracts before a candidate becomes a component.
    """
    node = ast.parse(ast.unparse(node)).body[0]
    names = {}
    for item in ast.walk(node):
        name = item.arg if isinstance(item, ast.arg) else item.id if isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store) else None
        if name is not None and name not in names:
            names[name] = f'v{len(names)}'
    class Normalize(ast.NodeTransformer):
        def visit_Name(self, item):
            item.id = names.get(item.id, item.id)
            return item
        def visit_arg(self, item):
            item.arg = names.get(item.arg, item.arg)
            return self.generic_visit(item)
        def generic_visit(self, item):
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if item.body and isinstance(item.body[0], ast.Expr) and isinstance(item.body[0].value, ast.Constant) and isinstance(item.body[0].value.value, str):
                    item.body = item.body[1:] or [ast.Pass()]
            return super().generic_visit(item)
    node = Normalize().visit(node)
    node.name = 'component'
    return ast.dump(node, include_attributes=False)


def mine(entries):
    clusters = {}
    parse_failures = 0
    for entry in entries:
        for ref in entry.references:
            if not ref.get('validated'):
                continue
            try:
                tree = ast.parse(ref['code'])
            except SyntaxError:
                parse_failures += 1
                continue
            for node in ast.walk(tree):
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    continue
                structure = normalized(node)
                key = hashlib.sha256(structure.encode()).hexdigest()
                cluster = clusters.setdefault(key, {'sha256': key, 'kind': type(node).__name__,
                    'ast_nodes': sum(1 for _ in ast.walk(node)), 'example_source': ast.unparse(node), 'provenance': []})
                cluster['provenance'].append({'key': entry.key, 'uid': ref.get('uid'),
                    'name': node.name, 'line': node.lineno, 'source_sha256': hashlib.sha256(ref['code'].encode()).hexdigest(),
                    'license': entry.license, 'attribution': entry.attribution})
    for cluster in clusters.values():
        cluster['problem_count'] = len({p['key'] for p in cluster['provenance']})
        cluster['family_count'] = len({splits.sibling_base(p['key'].removeprefix('lc:')) for p in cluster['provenance']})
    ranked = sorted(clusters.values(), key=lambda c: (-c['family_count'], -c['problem_count'], -c['ast_nodes'], c['sha256']))
    return ranked, parse_failures


def reserve(entries, used, count, seed):
    families = defaultdict(list)
    for entry in entries:
        families[splits.sibling_base(entry.slug)].append(entry)
    used_families = {splits.sibling_base(e.slug) for e in entries if e.key in used}
    buckets = defaultdict(list)
    for family, members in families.items():
        if family not in used_families and any(e.judge_uid for e in members):
            buckets[members[0].difficulty].append(family)
    for bucket in buckets.values():
        bucket.sort(key=lambda family: digest([seed, family]))
    chosen = []
    while len(chosen) < count and any(buckets.values()):
        for difficulty in sorted(buckets):
            if buckets[difficulty] and len(chosen) < count:
                chosen.append(buckets[difficulty].pop(0))
    if len(chosen) != count:
        raise ValueError('Not enough fresh confirmation families')
    confirmation = [e.key for family in chosen for e in families[family]]
    return confirmation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--confirmation-families', type=int, default=60)
    parser.add_argument('--seed', type=int, default=20261019)
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum() or args.confirmation_families < 1:
        raise ValueError('Invalid run name or confirmation size')
    print(f'[run-contract] run_name={args.name} pairs_input_spec=research-index '
          'resume_from=none resume_stage=none decode=none eval_dataset_paths=index-only '
          'device=cpu schedule=serial runtime_mode=cpu sweep_mode=after_train')
    entries = splits.read_index_entries()  # Never corpus_entries.
    manifest = splits.load_manifest()
    problems = splits.load_all()
    forbidden = splits.excluded_slugs(splits.solving_pools(problems))
    heldout = {uid for group in manifest['solving'].values() for uid in group}
    forbidden.update(problems[uid].slug for uid in heldout if problems[uid].slug)
    if any(e.slug in forbidden or heldout.intersection(e.members) for e in entries):
        raise ValueError('Held-out problem or alias reached research index')
    from .audit import dev_problems, require_frozen
    vocabulary_hash = require_frozen()
    dev_uids = {p.uid for p in dev_problems(problems)}
    used = {e.key for e in entries if dev_uids.intersection(e.members)}
    used.update(q.get('target') for q in manifest['recognition'] + manifest['recognition_dev'])
    confirmation = reserve(entries, used, args.confirmation_families, args.seed)
    source_hash = digest([e.__dict__ for e in entries])
    split = {'seed': args.seed, 'source_sha256': source_hash, 'confirmation_keys': confirmation,
             'v1_sha256': vocabulary_hash, 'unit': 'sibling family; stratified by difficulty'}
    directory = LANE_ROOT / 'runs' / args.name
    directory.mkdir(parents=True, exist_ok=True)
    frozen = directory / 'split.json'
    if frozen.exists() and json.loads(frozen.read_text()) != split:
        raise ValueError('Refusing to redraw an existing mining split')
    frozen.write_text(json.dumps(split, indent=2) + '\n')
    mining = [e for e in entries if e.key not in set(confirmation)]
    clusters, failures = mine(mining)
    with (directory / 'clusters.jsonl').open('w') as out:
        for cluster in clusters:
            out.write(json.dumps(cluster) + '\n')
    recurring = [c for c in clusters if len({p['key'] for p in c['provenance']}) >= 2]
    summary = {'source_sha256': source_hash, 'split_sha256': digest(split), 'v1_sha256': vocabulary_hash,
               'mining_entries': len(mining), 'mined_verified_entries': sum(any(r.get('validated') for r in e.references) for e in mining), 'confirmation_entries': len(confirmation),
               'clusters': len(clusters), 'recurring_clusters': len(recurring),
               'cross_family_recurring_clusters': sum(c['family_count'] >= 2 for c in clusters), 'parse_failures': failures,
               'evidence': 'structural candidates only; no new verified components or coverage claim',
               'top_recurring': [{k: c[k] for k in ('sha256', 'kind', 'ast_nodes', 'problem_count', 'family_count', 'provenance')} for c in recurring[:10]]}
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'top_recurring'}, indent=2))

if __name__ == '__main__':
    main()
