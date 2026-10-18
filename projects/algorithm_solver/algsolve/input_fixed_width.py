"""Freeze exactly 256 eight-bit tokens from already screened typing-study rows."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
from .input_vocabulary import COMMANDS, digest, encode, lexemes as python_lexemes
from .input_javascript import lexemes as javascript_lexemes


def fit(rows, language):
    lexemes = python_lexemes if language == 'python' else javascript_lexemes
    counts, families = Counter(), defaultdict(set)
    for row in rows:
        if row['split'] != 'train':
            continue
        for token in lexemes(row['text']):
            counts[token] += 1
            families[token].add(row['family'])
    eligible = [token for token in counts if len(families[token]) >= 3]
    shortcuts = sorted(eligible, key=lambda token: (-counts[token] * (len(token) - 1), token))[:123]
    if len(shortcuts) != 123:
        raise ValueError('Need 123 recurring shortcuts; never pad with unused entries')
    tokens = [chr(i) for i in range(128)] + sorted(shortcuts) + [c for c in COMMANDS if c != '<LITERAL_BYTE>']
    if len(tokens) != 256 or len(set(tokens)) != 256:
        raise ValueError('Expected 256 unique entries')
    return {'id': f'leetcode-{language}-byte256-v1', 'bits': 8, 'tokens': tokens}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rows', type=Path, required=True)
    parser.add_argument('--language', choices=['javascript', 'python'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-receipt', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Use a new immutable output directory')
    print(f'[run-contract] run_name={args.output.name} pairs_input_spec=previously-screened-reference-rows '
          'resume_from=none resume_stage=none decode=fixed8 eval_dataset_paths=family-development '
          'device=cpu schedule=fit-freeze-score runtime_mode=cpu sweep_mode=after_train', flush=True)
    rows = json.loads(args.rows.read_text())
    if any(row['split'] not in ('train', 'development') or not row['text'].isascii() for row in rows):
        raise ValueError('Only screened ASCII training/development rows are permitted')
    profile = fit(rows, args.language)
    book = {token: f'{index:08b}' for index, token in enumerate(profile['tokens'])}
    args.output.mkdir(parents=True)
    def write(name, value):
        (args.output / name).write_text(json.dumps(value, indent=2) + '\n')
    write('profile.json', profile)
    write('codebook.json', book)
    scores = {}
    for split in ('train', 'development'):
        texts = [row['text'] for row in rows if row['split'] == split]
        ascii_presses = sum(len(text)*7 for text in texts)
        presses = sum(encode(text, book)[0] for text in texts)
        scores[split] = {'files':len(texts), 'ascii_presses':ascii_presses, 'fixed8_presses':presses,
                         'saving_fraction':1-presses/ascii_presses}
    receipt = {'profile':profile['id'], 'profile_sha256':digest(profile), 'codebook_sha256':digest(book),
               'entries':256, 'presses_per_entry':8, 'ascii_ids':[0,127], 'shortcut_ids':[128,250],
               'command_ids':[251,255], 'escape_entries':0, 'scores':scores,
               'source_rows_sha256':hashlib.sha256(args.rows.read_bytes()).hexdigest(),
               'source_receipt_sha256':hashlib.sha256(args.source_receipt.read_bytes()).hexdigest(),
               'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'method':'123 frequency-times-length shortcuts recurring in at least three training families; fixed eight-bit IDs; exact minimum-token segmentation for cost',
               'limits':'Reuses previously explored reference splits, not fresh confirmation. Ideal error-free encoding only; no human productivity, global vocabulary optimum, or solving correctness claim.',
               'source':json.loads(args.source_receipt.read_text())}
    write('summary.json', receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k != 'source'}), flush=True)


if __name__ == '__main__':
    main()
