"""Fit binary typing vocabularies on permitted reference text, never test outputs."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import heapq
import json
from pathlib import Path
import re

from . import splits
from .synth import training_pairs

COMMANDS = ['<UNDO>', '<DELETE_INSERT>', '<LEFT>', '<RIGHT>', '<PAUSE>', '<LITERAL_BYTE>']


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def codes(weights):
    queue = [(weight, serial, token) for serial, (token, weight) in enumerate(sorted(weights.items()))]
    heapq.heapify(queue)
    serial = len(queue)
    while len(queue) > 1:
        a, b = heapq.heappop(queue), heapq.heappop(queue)
        heapq.heappush(queue, (a[0] + b[0], serial, (a[2], b[2])))
        serial += 1
    result = {}
    def visit(node, prefix):
        if isinstance(node, str):
            result[node] = prefix
        else:
            visit(node[0], prefix + '0')
            visit(node[1], prefix + '1')
    visit(queue[0][2], '')
    return result


def encode(text, book):
    choices = defaultdict(list)
    for token, bits in book.items():
        if token not in COMMANDS:
            choices[token[0]].append((token, len(bits)))
    cost = [float('inf')] * len(text) + [0]
    next_token = [''] * len(text)
    for i in range(len(text) - 1, -1, -1):
        for token, width in choices[text[i]]:
            candidate = width + cost[i + len(token)] if text.startswith(token, i) else float('inf')
            if candidate < cost[i] or candidate == cost[i] and (-len(token), token) < (-len(next_token[i]), next_token[i]):
                cost[i], next_token[i] = candidate, token
    if cost[0] == float('inf'):
        raise ValueError('Non-ASCII input')
    counts = Counter()
    i = 0
    while i < len(text):
        token = next_token[i]
        counts[token] += 1
        i += len(token)
    return cost[0], counts


def lexemes(text):
    return re.findall(r'[A-Za-z_][A-Za-z_0-9]+|\n +| {2,}|==|!=|<=|>=|//|\*\*|:=|->|\+=|-=|=>|===', text)


def fit(texts, shortcut_count=122):
    # Bounded shortcut budget; candidates are identifiers, operators and indent runs.
    if not 1 <= shortcut_count <= 122:
        raise ValueError("Total vocabulary exceeds 256 entries")
    counts = Counter(token for text in texts for token in lexemes(text))
    shortcuts = sorted(counts, key=lambda t: (-counts[t] * (len(t) - 1), t))[:shortcut_count]
    char_counts = Counter(''.join(texts))
    weights = {chr(i): max(1, char_counts[chr(i)]) for i in range(128)}
    weights.update({token: counts[token] for token in shortcuts})
    command_weight = max(1, sum(char_counts.values()) // 1000)
    weights.update({token: command_weight for token in COMMANDS})
    best, best_cost = weights, float('inf')
    for _ in range(6):
        book = codes(weights)
        total, uses = 0, Counter()
        for text in texts:
            cost, count = encode(text, book)
            total += cost
            uses.update(count)
        if total < best_cost:
            best, best_cost = dict(weights), total
        weights = {token: command_weight if token in COMMANDS else max(1, uses[token]) for token in weights}
    return best


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--confirmation', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--shortcuts', type=int, default=122)
    args = parser.parse_args()
    if not 1 <= args.shortcuts <= 122:
        raise ValueError('128 ASCII + six commands + shortcuts must fit in 256 entries')
    if args.output.exists():
        raise ValueError('Use a new immutable run directory')
    print(f'[run-contract] run_name={args.output.name} pairs_input_spec=permitted-research-index '
          'resume_from=none resume_stage=none decode=deterministic eval_dataset_paths=family-hash-development '
          'device=cpu schedule=fit-then-score runtime_mode=cpu sweep_mode=after_train', flush=True)
    entries, problems, manifest = splits.read_index_entries(), splits.load_all(), splits.load_manifest()
    allowed = training_pairs.policy(entries, problems, manifest, json.loads(args.confirmation.read_text()), set(problems))
    unique = {e.key: e for e in allowed.values()}
    rows = []
    for key, entry in sorted(unique.items()):
        refs = sorted((r for r in entry.references if r.get('validated')), key=lambda r: (r['source'], r['uid']))
        if not refs or not refs[0]['code'].isascii():
            continue
        family = splits.sibling_base(entry.slug)
        rows.append({'key': key, 'family': family, 'text': refs[0]['code'], 'license': entry.license,
                     'attribution': entry.attribution, 'split': 'development' if int(digest(family)[:8], 16) % 5 == 0 else 'train'})
    # Identical code must not cross the encoding study's own split either.
    dev_hashes = {digest(r['text']) for r in rows if r['split'] == 'development'}
    rows = [r for r in rows if r['split'] == 'development' or digest(r['text']) not in dev_hashes]
    train = [r['text'] for r in rows if r['split'] == 'train']
    if not train or not any(r['split'] == 'development' for r in rows):
        raise ValueError('Empty split')
    weights = fit(train, args.shortcuts)
    book = codes(weights)
    scores = {}
    for split in ['train', 'development']:
        texts = [r['text'] for r in rows if r['split'] == split]
        ascii_presses = sum(len(text) * 7 for text in texts)
        presses = sum(encode(text, book)[0] for text in texts)
        scores[split] = {'files': len(texts), 'ascii_presses': ascii_presses, 'huffman_presses': presses,
                         'saving_fraction': 1 - presses / ascii_presses}
    profile = {'id': f'leetcode-python-lexical{args.shortcuts}-v2', 'weights': sorted(weights.items())}
    receipt = {'profile': profile['id'], 'profile_sha256': digest(profile), 'scores': scores,
               'confirmation_sha256': hashlib.sha256(args.confirmation.read_bytes()).hexdigest(),
               'source_rows_sha256': digest(rows), 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'method': f'{args.shortcuts} frequency-times-length shortcuts; six training-only DP/refit iterations; minimum training cost chosen',
               'limits': 'Error-free optimal segmentation for this fixed codebook only; no measured human effort or global optimum. Development is not protected solver confirmation.',
               'policy': 'Existing research exclusions plus reserved/recognition sibling families; ASCII validated reference text only; no hidden outputs.'}
    args.output.mkdir(parents=True, exist_ok=True)
    for name, value in [('profile.json', profile), ('summary.json', receipt), ('source-rows.json', rows)]:
        (args.output / name).write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(receipt), flush=True)


if __name__ == '__main__':
    main()
