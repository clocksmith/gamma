"""Pinned source acquisition for the binary-input study; never executes solutions.

Raw sources and manifests remain in ignored data/raw/. This is acquisition only:
research training must still exclude protected problems, aliases and families.
"""
from __future__ import annotations

import concurrent.futures
import hashlib
import json
import urllib.parse
from pathlib import Path

from .fetch import DOOCS_COMMIT, DOOCS_REPO, RAW_DIR, git_blob_sha, http_get


def fetch() -> dict:
    target = RAW_DIR / 'doocs__leetcode_input' / DOOCS_COMMIT
    target.mkdir(parents=True, exist_ok=True)
    print('[run-contract] run_name=binary-input-source-v1 '
          f'pairs_input_spec=github:{DOOCS_REPO}@{DOOCS_COMMIT} '
          'resume_from=verified-files resume_stage=fetch decode=none '
          'eval_dataset_paths=none device=cpu schedule=fetch-only '
          'runtime_mode=cpu sweep_mode=after_train', flush=True)
    api = f'https://api.github.com/repos/{DOOCS_REPO}'

    def listing(name: str, url: str) -> dict:
        path = target / name
        if not path.exists():
            path.write_bytes(http_get(url, 'application/vnd.github+json'))
        result = json.loads(path.read_bytes())
        if result.get('truncated'):
            raise ValueError('Truncated source tree')
        return result

    root = listing('root-tree.json', f'{api}/git/trees/{DOOCS_COMMIT}')
    solution = next(e for e in root['tree'] if e['path'] == 'solution')
    tree = listing('solution-tree.json', f"{api}/git/trees/{solution['sha']}?recursive=1")
    wanted = [dict(entry, path='solution/' + entry['path']) for entry in tree['tree']
              if entry['type'] == 'blob' and entry['path'].endswith(('.js', '.ts'))]
    wanted += [entry for entry in root['tree'] if entry['type'] == 'blob'
               and (entry['path'].upper().startswith('LICENSE') or entry['path'] == 'README_EN.md')]
    if len(wanted) > 10000 or sum(e.get('size', 0) for e in wanted) > 100_000_000:
        raise ValueError('Source acquisition exceeded its declared cap')

    def one(entry: dict) -> dict:
        path = target / entry['path']
        if not path.resolve().is_relative_to(target.resolve()):
            raise ValueError('Source path escapes target')
        data = path.read_bytes() if path.exists() else b''
        if git_blob_sha(data) != entry['sha']:
            url = f'https://raw.githubusercontent.com/{DOOCS_REPO}/{DOOCS_COMMIT}/{urllib.parse.quote(entry["path"])}'
            data = http_get(url)
            if git_blob_sha(data) != entry['sha']:
                raise ValueError(f'Pinned blob mismatch: {entry["path"]}')
            path.parent.mkdir(parents=True, exist_ok=True)
            temporary = path.with_suffix(path.suffix + '.partial')
            temporary.write_bytes(data)
            temporary.replace(path)
        return {'path': entry['path'], 'bytes': len(data), 'git_blob_sha': entry['sha'],
                'sha256': hashlib.sha256(data).hexdigest()}

    files = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        for record in pool.map(one, wanted):
            files.append(record)
            if len(files) % 250 == 0:
                print(f'[fetch] verified {len(files)}/{len(wanted)}', flush=True)
    manifest = {'source': DOOCS_REPO, 'revision': DOOCS_COMMIT, 'files': files,
                'bytes': sum(f['bytes'] for f in files),
                'language_counts': {suffix: sum(f['path'].endswith(suffix) for f in files)
                                    for suffix in ['.js', '.ts']},
                'license': 'CC-BY-SA-4.0; retain source LICENSE and README terms',
                'evidence': 'hash-verified source only; not syntax, execution or correctness qualification',
                'training_policy': 'No fitting before protected-family exclusion and train/development split'}
    temporary = target / 'manifest.json.partial'
    temporary.write_text(json.dumps(manifest, indent=2) + '\n')
    temporary.replace(target / 'manifest.json')
    print(json.dumps({k: v for k, v in manifest.items() if k != 'files'}), flush=True)
    return manifest


if __name__ == '__main__':
    fetch()
