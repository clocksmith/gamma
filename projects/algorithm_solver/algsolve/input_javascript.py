"""Index-only JavaScript encoding experiment; never a solver coverage claim.

Reserve families from metadata before reading source. Freeze the selected profile
without opening confirmation text. Raw sources, exclusions and per-file results
remain in ignored runs; only compact receipts may be published.
"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

from . import splits
from .input_vocabulary import COMMANDS, codes, digest, encode
from .synth.training_pairs import policy

# This is a lexical candidate screen, not a JavaScript parser. Conservatively
# omit whole strings/templates/comments; syntax qualification uses Node below.
LEXEMES = re.compile(
    r'//[^\n]*|/\*[\s\S]*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`'
    r'|[A-Za-z_$][\w$]+|\n +| {2,}|===|!==|>>>|=>|==|!=|<=|>=|\+\+|--|&&|\|\||\?\?|\+=|-=|\*\*')


def lexemes(text):
    return [m.group() for m in LEXEMES.finditer(text)
            if not m.group().startswith(('//', '/*', '"', "'", '`'))]


def reserve(files, allowed, count):
    """Use identities/checksums only; do not open any source or expected output."""
    rows = []
    for file in files:
        path = PurePosixPath(file['path'])
        if path.suffix != '.js':
            continue
        entry = allowed.get(path.parent.name.split('.')[0])
        if entry is None:
            continue
        rows.append({**file, 'key': entry.key, 'family': splits.sibling_base(entry.slug),
                     'tags': entry.tags})
    families = sorted({r['family'] for r in rows}, key=lambda f: digest(['js-confirmation-v1', f]))
    if count < 1 or len(families) <= count:
        raise ValueError('Insufficient distinct families for confirmation and fitting')
    protected = set(families[:count])
    for row in rows:
        row['split'] = ('confirmation' if row['family'] in protected else
                        'development' if int(digest(row['family'])[:8], 16) % 5 == 0 else 'train')
    # Identical sources cannot cross the split, even under unrelated titles.
    confirmation_hashes = {r['sha256'] for r in rows if r['split'] == 'confirmation'}
    development_hashes = {r['sha256'] for r in rows if r['split'] == 'development'}
    excluded = []
    for row in rows:
        if row['split'] != 'confirmation' and row['sha256'] in confirmation_hashes:
            row['reason'] = 'identical_confirmation_source'; excluded.append(row)
        elif row['split'] == 'train' and row['sha256'] in development_hashes:
            row['reason'] = 'identical_development_source'; excluded.append(row)
    rows = [r for r in rows if 'reason' not in r]
    # One problem per selected family is the scoring denominator. All sibling
    # problems and all alternative files remain withheld from fitting.
    selected = [min((r for r in rows if r['family'] == family), key=lambda r: (r['key'], r['path']))
                for family in families[:count]]
    return rows, selected, excluded


def read_development(root, rows, node):
    accepted, rejected = [], []
    for row in rows:
        if row['split'] == 'confirmation':
            continue
        path = (root / row['path']).resolve()
        if not path.is_relative_to(root.resolve()):
            raise ValueError('Source path escapes pinned root')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError(f'Source hash mismatch: {row["path"]}')
        text = data.decode('utf-8')
        if not text.isascii():
            rejected.append({**row, 'reason': 'non_ascii'}); continue
        checked = subprocess.run([node, '--check', '--input-type=commonjs'], input=text,
                                 text=True, capture_output=True, timeout=10)
        if checked.returncode:
            rejected.append({**row, 'reason': 'syntax', 'detail': checked.stderr[:1000]}); continue
        accepted.append({**row, 'text': text})
    if not all(any(r['split'] == split for r in accepted) for split in ['train', 'development']):
        raise ValueError('Empty qualified fitting/development split')
    return accepted, rejected


def fit(rows, budget):
    counts, families = Counter(), defaultdict(set)
    for row in rows:
        for token in lexemes(row['text']):
            counts[token] += 1
            families[token].add(row['family'])
    # A shortcut must recur across three problem families, not just repeated
    # alternative implementations of one problem.
    eligible = [t for t in counts if len(families[t]) >= 3]
    shortcuts = sorted(eligible, key=lambda t: (-counts[t] * (len(t) - 1), t))[:budget]
    chars = Counter(''.join(r['text'] for r in rows))
    command_weight = max(1, sum(chars.values()) // 1000)
    weights = {chr(i): max(1, chars[chr(i)]) for i in range(128)}
    weights.update({t: counts[t] for t in shortcuts})
    weights.update({t: command_weight for t in COMMANDS})
    best, best_cost = None, float('inf')
    for _ in range(6):
        book, uses, total = codes(weights), Counter(), 0
        for row in rows:
            cost, used = encode(row['text'], book)
            total += cost; uses.update(used)
        if total < best_cost:
            best, best_cost = dict(weights), total
        weights = {t: command_weight if t in COMMANDS else max(1, uses[t]) for t in weights}
    return best, {t: len(families[t]) for t in shortcuts}


def score(rows, book):
    results = []
    for row in rows:
        presses, uses = encode(row['text'], book)
        results.append({k: row[k] for k in ['key', 'family', 'path', 'sha256', 'tags', 'split']} | {
            'characters': len(row['text']), 'ascii_presses': 7 * len(row['text']),
            'presses': presses, 'tokens': sum(uses.values()),
            'execution': 'not_run', 'skeleton_family': None, 'hole_nodes': None,
            'human_hints': None, 'human_presses': None})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--confirmation', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True, help='Exported deployed JS token-to-bit map')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--node', default='node')
    parser.add_argument('--reserve', type=int, default=150)
    parser.add_argument('--prior-exposure', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Run already exists; use a new immutable run directory')
    entries, problems, manifest = splits.read_index_entries(), splits.load_all(), splits.load_manifest()
    permitted = policy(entries, problems, manifest, json.loads(args.confirmation.read_text()), set(problems))
    allowed = {uid.split(':')[1]: entry for uid, entry in permitted.items() if uid.startswith('doocs:')}
    source_manifest = json.loads((args.source / 'manifest.json').read_text())
    rows, selected, excluded = reserve(source_manifest['files'], allowed, args.reserve)
    args.output.mkdir(parents=True)
    def write(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    contract = {'schema': 'algsolve.js-input.v1', 'source': source_manifest['source'],
                'revision': source_manifest['revision'], 'source_manifest_sha256':
                hashlib.sha256((args.source / 'manifest.json').read_bytes()).hexdigest(),
                'policy_confirmation_sha256': hashlib.sha256(args.confirmation.read_bytes()).hexdigest(),
                'files': rows, 'confirmation_selected': selected, 'excluded': excluded,
                'budgets': [122], 'minimum_family_support': 3, 'refit_rounds': 6,
                'selection': 'user-fixed 256-entry budget: 128 ASCII, six commands, 122 recurring shortcuts',
                'exposure': 'Reserved within this run; earlier binary-javascript-v2 explored overlapping source. This is not globally untouched confirmation.',
                'prior_exposure_sha256': hashlib.sha256(args.prior_exposure.read_bytes()).hexdigest(),
                'limits': 'Sibling grouping and exact-byte duplicate exclusion do not establish semantic novelty',
                'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    write('contract.json', contract)
    print(f'[run-contract] run_name={args.output.name} pairs_input_spec=pinned-permitted-js-index '
          'resume_from=none resume_stage=none decode=deterministic eval_dataset_paths=index-development '
          'device=cpu schedule=reserve-fit-freeze runtime_mode=cpu sweep_mode=after_train', flush=True)
    qualified, rejected = read_development(args.source, rows, args.node)
    write('source-rows.json', qualified); write('rejected.json', rejected)
    baseline = json.loads(args.baseline.read_text())
    baseline_rows = score(qualified, baseline)
    write('baseline-rows.json', baseline_rows)
    candidates = []
    for budget in contract['budgets']:
        weights, support = fit([r for r in qualified if r['split'] == 'train'], budget)
        book = codes(weights)
        results = score(qualified, book)
        profile = {'id': f'doocs-js-family-lexical{budget}-v3', 'weights': sorted(weights.items())}
        summary = {'budget': budget, 'shortcuts': len(support), 'profile_sha256': digest(profile),
                   'scores': {split: {metric: sum(r[metric] for r in results if r['split'] == split)
                                       for metric in ['characters', 'ascii_presses', 'presses', 'tokens']}
                              for split in ['train', 'development']}}
        write(f'candidate-{budget}.json', {'profile': profile, 'book': book, 'family_support': support,
                                         'summary': summary, 'rows': results})
        candidates.append((summary['scores']['development']['presses'], budget, profile, book, summary))
        print(json.dumps(summary), flush=True)
    _, budget, profile, book, _ = min(candidates)
    write('profile.json', profile); write('codebook.json', book)
    receipt = {'schema': contract['schema'], 'selected_budget': budget, 'profile_sha256': digest(profile),
               'codebook_sha256': digest(book), 'contract_sha256': digest(contract),
               'baseline_codebook_sha256': digest(baseline),
               'candidates': [c[-1] for c in candidates],
               'counts': dict(Counter(r['split'] for r in qualified)), 'rejected': len(rejected),
               'confirmation_problems': len(selected), 'confirmation_opened': False,
               'baseline_scores': {s: sum(r['presses'] for r in baseline_rows if r['split'] == s)
                                   for s in ['train', 'development']},
               'scope': 'Ideal error-free encoding, syntax-checked index references only; no passing compositions, human effort, or unfamiliar solving measured'}
    write('freeze.json', receipt)
    print(json.dumps(receipt), flush=True)
    # Score only after profile/codebook/freeze files are written. Preserve prior exposure.
    exposed = {r['source']['path'] for r in json.loads(args.prior_exposure.read_text())}
    reserved_rows, skipped = [], []
    for row in selected:
        data = (args.source / row['path']).read_bytes()
        if hashlib.sha256(data).hexdigest() != row['sha256']:
            raise ValueError('Reserved source hash mismatch')
        text = data.decode('utf-8')
        checked = subprocess.run([args.node, '--check', '--input-type=commonjs'], input=text,
                                 text=True, capture_output=True, timeout=10)
        if not text.isascii() or checked.returncode:
            skipped.append(row['path']); continue
        reserved_rows.append({**row, 'text': text})
    selected_scores = score(reserved_rows, book)
    legacy_scores = score(reserved_rows, baseline)
    after_freeze = {'profile_sha256': digest(profile), 'files': len(reserved_rows),
                    'excluded_files': skipped,
                    'prior_exposed_files': sum(r['path'] in exposed for r in reserved_rows),
                    'ascii_presses': sum(r['ascii_presses'] for r in selected_scores),
                    'candidate_presses': sum(r['presses'] for r in selected_scores),
                    'legacy_presses': sum(r['presses'] for r in legacy_scores),
                    'scope': 'Post-freeze score within this run; overlapping prior exploration prevents globally fresh confirmation or human-productivity claims.'}
    write('reserved-score.json', after_freeze)
    write('reserved-rows.json', selected_scores)
    print(json.dumps(after_freeze), flush=True)


if __name__ == '__main__':
    main()
