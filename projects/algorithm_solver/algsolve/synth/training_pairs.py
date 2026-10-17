"""Requalify permitted development audit proposals as bounded graph targets.

Reads the research index only. Every emitted graph is compiled under the current
frozen vocabulary and freshly passes public and independent development tests.
Hidden tests never enter exported model inputs. No model calls or training.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from .. import splits
from ..records import LANE_ROOT, load_hidden_tests
from . import audit, graph_targets, mine, render


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def policy(entries, problems, manifest, confirmation, dev_uids):
    if confirmation['source_sha256'] != mine.digest([e.__dict__ for e in entries]):
        raise ValueError('Research index differs from the reserved confirmation split')
    heldout = {uid for group in manifest['solving'].values() for uid in group}
    forbidden_slugs = splits.excluded_slugs(splits.solving_pools(problems))
    forbidden_slugs.update(problems[uid].slug for uid in heldout if problems[uid].slug)
    reserved = {key.removeprefix('lc:') for key in confirmation['confirmation_keys']}
    for query in manifest['recognition'] + manifest['recognition_dev']:
        if query.get('target'):
            reserved.add(query['target'].removeprefix('lc:'))
        elif query.get('problem_uid'):
            reserved.add(problems[query['problem_uid']].slug)
    families = {splits.sibling_base(slug) for slug in forbidden_slugs | reserved if slug}
    if any(e.slug in forbidden_slugs or heldout.intersection(e.members) for e in entries):
        raise ValueError('Held-out alias reached research index')
    allowed = {}
    for entry in entries:
        if splits.sibling_base(entry.slug) in families:
            continue
        for uid in set(entry.members) & set(dev_uids):
            if uid not in heldout and problems[uid].slug == entry.slug:
                allowed[uid] = entry
    return allowed


def pattern(target):
    # Omit symbol names/constants while retaining AST operators and port topology.
    def shape(value):
        if isinstance(value, list):
            return [shape(v) for v in value]
        if isinstance(value, dict):
            if 'op' in value:
                return {'op': value['op'], 'children': {k: shape(v) for k, v in value['fields'].items()
                        if isinstance(v, (dict, list))}}
            return {k: shape(v) for k, v in value.items()}
        return type(value).__name__
    structure = [{'component': slot['component'],
                  'bindings': [b['source'] for b in slot.get('bindings', [])],
                  'parameters': {name: shape(value) for name, value in slot.get('parameters', {}).items()}}
                 for slot in target['slots']]
    return mine.digest([structure, shape(target['answer'])])


def candidate(row, allowed, problems, vocabulary, check=audit.check_composition):
    if row.get('uid') not in allowed:
        return None, 'not_permitted_development'
    if row.get('label') != 'demonstrated_expressible' or not row.get('composition'):
        return None, 'no_demonstrated_composition'
    problem = problems[row['uid']]
    if problem.evidence_ceiling != 'independent_tests_passed' or not problem.public_tests or not load_hidden_tests(problem):
        return None, 'missing_independent_or_public_tests'
    params = [p[0] for p in problem.params]
    try:
        target = graph_targets.encode(row['composition'], method=problem.entry.get('method'), params=params,
                                      vocabulary_sha256=vocabulary)
        composition = graph_targets.decode(target, params=params, vocabulary_sha256=vocabulary)
        compiled = graph_targets.compile_target(target, method=problem.entry.get('method'), params=params,
                                                vocabulary_sha256=vocabulary)
        original = render.render(row['composition'], method=problem.entry.get('method'), params=params)
        if compiled.source != original.source:
            return None, 'graph_round_trip_changed_program'
    except (ValueError, SyntaxError, KeyError, TypeError) as error:
        return None, 'unqualified_graph: ' + str(error)
    # Prior audit claims are proposals only. Current rendered code must pass again.
    checked = check(problem, composition)
    if not checked.get('ok') or checked.get('evidence') != 'independent_tests_passed':
        return None, 'fresh_validation_failed'
    if checked['rendered']['source_sha256'] != graph_targets.source_hash(compiled):
        raise ValueError('Judge receipt is not bound to the compiled graph')
    if not (checked.get('public') or {}).get('passed') or not (checked.get('hidden') or {}).get('passed'):
        raise ValueError('Independent evidence lacks passing public/hidden receipts')
    family = pattern(target)
    entry = allowed[problem.uid]
    return {'schema': 'algsolve.composition-pair.v1', 'uid': problem.uid, 'key': entry.key,
            'input': {'statement': problem.statement, 'starter_code': problem.starter_code,
                      'params': problem.params, 'public_examples': problem.public_tests},
            'target': target, 'pattern_sha256': family,
            'provenance': {'license': entry.license, 'attribution': entry.attribution,
                           'source_vocabulary_sha256': row.get('vocabulary_sha256'),
                           'current_vocabulary_sha256': vocabulary,
                           'rendered_source_sha256': graph_targets.source_hash(compiled),
                           'development_hidden_tests_sha256': mine.digest(load_hidden_tests(problem)),
                           'public_tests_passed': checked['public'].get('tests_passed'),
                           'independent_tests_passed': checked['hidden'].get('tests_passed'),
                           'proposer': row.get('proposer'),
                           'qualification': 'fresh development tests; finite test evidence, not formal correctness'}}, None


def assign_splits(pairs):
    # Keep every alternative for the same problem together, and transitively
    # every problem sharing a structural pattern. No arbitrary gold preference.
    parent = {}
    def root(key):
        parent.setdefault(key, key)
        while parent[key] != key:
            key = parent[key]
        return key
    for pair in pairs:
        identities = ['uid:' + pair['uid'], 'pattern:' + pair['pattern_sha256']]
        if pair.get('problem_family'):
            identities.append('family:' + pair['problem_family'])
        for identity in identities[1:]:
            left, right = root(identities[0]), root(identity)
            if left != right:
                parent[max(left, right)] = min(left, right)
    groups = {}
    for key in parent:
        groups.setdefault(root(key), []).append(key)
    identities = {key: mine.digest(sorted(members)) for key, members in groups.items()}
    for pair in pairs:
        group = identities[root('uid:' + pair['uid'])]
        pair['split_group_sha256'] = group
        pair['learning_split'] = 'pattern_confirmation' if int(group[:8], 16) % 5 == 0 else 'training'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, action='append', required=True)
    parser.add_argument('--confirmation', type=Path, required=True)
    parser.add_argument('--name', required=True)
    args = parser.parse_args()
    if not args.name.replace('-', '').replace('_', '').isalnum():
        raise ValueError('Invalid run name')
    vocabulary = audit.require_frozen()
    entries, problems, manifest = splits.read_index_entries(), splits.load_all(), splits.load_manifest()
    confirmation = json.loads(args.confirmation.read_text())
    allowed = policy(entries, problems, manifest, confirmation, {p.uid for p in audit.dev_problems(problems)})
    sources = {str(p.resolve()): sha(p) for p in args.audit}
    output = LANE_ROOT/'runs'/args.name
    output.mkdir(parents=True, exist_ok=False)  # Never overwrite a dataset or its evidence.
    contract = {'vocabulary_sha256': vocabulary, 'audits': sources, 'confirmation_sha256': sha(args.confirmation),
                'manifest_sha256': mine.digest(manifest), 'research_index_sha256': mine.digest([e.__dict__ for e in entries]),
                'source_sha256': {name: sha(Path(__file__).parent/name) for name in ['training_pairs.py', 'graph_targets.py']},
                'limits': {'stage_slots': render.MAX_STAGES, 'hole_ast_nodes': graph_targets.MAX_HOLE_NODES},
                'pattern_split': 'connected problem/pattern groups: sha256(first 8 hex) mod 5 == 0 reserved',
                'model_input_policy': 'statement, starter, parameter types and public examples only',
                'status': 'building'}
    (output/'contract.json').write_text(json.dumps(contract, indent=2)+'\n')
    print(f'[run-contract] run_name={args.name} pairs_input_spec=permitted-development-audits '
          f'vocabulary={vocabulary} decode=none device=cpu runtime_mode=linux-sandbox '
          'schedule=serial model_calls=0 training=none', flush=True)
    counts, seen, uids, pairs = Counter(), set(), set(), []
    for path in args.audit:
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            row = json.loads(line)
            identity = mine.digest([row.get('uid'), row.get('composition')])
            if identity in seen:
                counts['duplicate_proposal'] += 1
                continue
            seen.add(identity)
            pair, reason = candidate(row, allowed, problems, vocabulary)
            if reason:
                counts[reason] += 1
                continue
            pair['provenance']['audit'] = {'sha256': sources[str(path.resolve())], 'line': line_number}
            pairs.append(pair)
            uids.add(pair['uid'])
            print(f'[pair] {pair["uid"]} requalified', flush=True)
    assign_splits(pairs)
    with (output/'pairs.jsonl').open('w') as stream:
        for pair in pairs:
            stream.write(json.dumps(pair, allow_nan=False)+'\n')
            counts['pairs'] += 1
            counts[pair['learning_split']] += 1
    summary = {'status': 'complete', 'counts': dict(counts), 'distinct_problems': len(uids),
               'pairs_sha256': sha(output/'pairs.jsonl'), 'contract_sha256': sha(output/'contract.json'),
               'limits': ['Target export and requalification only; no neural predictor trained.',
                          'Functional IO only; vocabulary v1 unchanged.',
                          'Structural pattern exclusion does not establish all semantic-pattern novelty.',
                          'A small dataset is not evidence of learnable coverage or fast solving.']}
    (output/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
