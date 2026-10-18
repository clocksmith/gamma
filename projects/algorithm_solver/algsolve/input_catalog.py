"""Export public challenge navigation metadata, without solutions or test data."""
import argparse
import hashlib
import json
from pathlib import Path
from .splits import DERIVED


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    source = DERIVED / 'corpus_entries.jsonl'
    rows = [json.loads(line) for line in source.read_text().splitlines()]
    print('[run-contract] run_name=binary-challenge-catalog-v1 pairs_input_spec=corpus_entries '
          'resume_from=none resume_stage=none decode=none eval_dataset_paths=none '
          'device=cpu schedule=metadata-only runtime_mode=cpu sweep_mode=after_train')
    catalog = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
               'scope': 'Known-problem navigation; no hidden tests, solutions, judge or solver endpoint.',
               'problems': [{key: row[key] for key in ['slug', 'title', 'difficulty']} for row in rows]}
    args.output.write_text(json.dumps(catalog, separators=(',', ':')) + '\n')
    print(f'Exported {len(rows)} challenge links')


if __name__ == '__main__':
    main()
