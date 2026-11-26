#!/usr/bin/env python3
"""Select the one untouched project. Run by the scorer, never by the trainer.

    python3 -I select_project.py --work WORKDIR

Six candidate repositories were named, pinned to a commit and ordered by
SHA-256("bits-objective-holdout-v1:project:" + "owner/repo") before any of
them was downloaded. None has been used by an earlier BITS experiment. The
first candidate in that order with at least MIN_FILES eligible files is the
project; the others are not opened. Eligible: a regular file with the
project's source extension, valid UTF-8, no NUL byte, 64 to 4,096 bytes (the
CodeNet rule). If more than MAX_FILES are eligible, the MAX_FILES with the
smallest SHA-256("bits-objective-holdout-v1:file:" + path) are kept. A file
that equals a training, development or fresh CodeNet file exactly or after
removing whitespace is dropped and counted.

Writes corpus/project/ and sets/project.json. Standard library only.
"""
import argparse
import hashlib
import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
LITERALS = HERE.parent

SEED = 'bits-objective-holdout-v1:'
MIN_BYTES, MAX_BYTES = 64, 4096
MIN_FILES, MAX_FILES = 100, 200
CANDIDATES = {
    'expressjs/express': ('1faf228935aa0a13111f92c28ee795be64ce3f0f', '4.21.2', 'MIT', 'javascript', '.js'),
    'jashkenas/underscore': ('d2e7e613a597bec6b16c946e42c91950dcc1a215', '1.13.7', 'MIT', 'javascript', '.js'),
    'ramda/ramda': ('980b3bf7712adb8ad8b5d9b2c6aca525cb3cf143', 'v0.30.1', 'MIT', 'javascript', '.js'),
    'psf/requests': ('0e322af87745eff34caffe4df68456ebc20d9068', 'v2.32.3', 'Apache-2.0', 'python', '.py'),
    'pallets/click': ('934813e4d421071a1b3db3973c02fe2721359a6e', '8.1.8', 'BSD-3-Clause', 'python', '.py'),
    'TheAlgorithms/Python': ('30507bbe41397065728167fb09aa820f9fce8dc7', 'master on 2026-11-11', 'MIT', 'python', '.py'),
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def squeezed(raw):
    return sha256(b''.join(raw.split()))


def order():
    return sorted(CANDIDATES, key=lambda r: sha256((SEED + 'project:' + r).encode()))


def eligible_files(repo, work):
    commit, _, _, _, ext = CANDIDATES[repo]
    dst = work / (repo.replace('/', '__') + '-' + commit[:12] + '.tar.gz')
    if not dst.exists():
        req = urllib.request.Request(f'https://codeload.github.com/{repo}/tar.gz/{commit}',
                                     headers={'User-Agent': 'generic-client/1.0'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            dst.write_bytes(resp.read())
    blob = dst.read_bytes()
    out = {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:gz') as tar:
        for member in tar:
            if not member.isfile() or not member.name.endswith(ext):
                continue
            rel = member.name.split('/', 1)[1] if '/' in member.name else member.name
            if not MIN_BYTES <= member.size <= MAX_BYTES:
                continue
            raw = tar.extractfile(member).read()
            if b'\x00' in raw:
                continue
            try:
                raw.decode('utf-8')
            except UnicodeDecodeError:
                continue
            out[rel] = raw
    return out, sha256(blob)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)

    seen_exact, seen_squeezed = set(), set()
    for spec, root in ((HERE / 'frozen' / 'sets' / 'train.json', LITERALS),
                       (HERE / 'frozen' / 'sets' / 'dev.json', LITERALS),
                       (HERE / 'sets' / 'fresh.json', HERE)):
        for f in json.loads(spec.read_text())['files']:
            raw = (root / f['path']).read_bytes()
            seen_exact.add(sha256(raw))
            seen_squeezed.add(squeezed(raw))

    tried = []
    for repo in order():
        files, tar_sha = eligible_files(repo, work)
        tried.append({'repository': repo, 'commit': CANDIDATES[repo][0], 'tarball_sha256': tar_sha,
                      'eligible_files': len(files)})
        if len(files) < MIN_FILES:
            continue
        commit, version, licence, lang, ext = CANDIDATES[repo]
        keep = sorted(files, key=lambda p: sha256((SEED + 'file:' + p).encode()))
        dropped = [p for p in keep if sha256(files[p]) in seen_exact or squeezed(files[p]) in seen_squeezed]
        keep = [p for p in keep if p not in set(dropped)][:MAX_FILES]
        out_dir = HERE / 'corpus' / 'project'
        out_dir.mkdir(parents=True, exist_ok=True)
        recs = []
        for i, p in enumerate(sorted(keep)):
            raw = files[p]
            rel = f'corpus/project/{i:04d}{ext}'
            (HERE / rel).write_bytes(raw)
            recs.append({'path': rel, 'unit': p, 'lang': lang, 'bytes': len(raw), 'sha256': sha256(raw),
                         'source_path': p})
        (HERE / 'sets' / 'project.json').write_text(json.dumps({
            'set': 'project',
            'source': f'{repo} at {commit} ({version}), licence {licence}',
            'unit': 'source file',
            'selection': {'candidate_order': order(), 'tried': tried, 'eligible_files': len(files),
                          'dropped_as_duplicates': dropped, 'kept': len(recs)},
            'files': recs,
        }, indent=1) + '\n')
        print(f'project: {repo} at {commit[:12]}, {len(files)} eligible, {len(recs)} kept, '
              f'{sum(r["bytes"] for r in recs)} bytes')
        return
    raise SystemExit('no candidate has enough eligible files')


if __name__ == '__main__':
    main()
