#!/usr/bin/env python3
"""Select two untouched projects, one Python and one JavaScript.
Run by the scorer after the dictionaries are frozen, never by the trainer.

    python3 -I select_projects.py --work WORKDIR

Candidates, pins, eligibility and file order are the objective-holdout-v1 rule
(imported unchanged from select_project.py). That experiment used only
expressjs/express and opened no other candidate. Here, for each language, the
first candidate in the frozen candidate order other than Express with at least
MIN_FILES eligible files is taken; up to MAX_FILES files are kept by the frozen
file order. A file equal to a train, dev, fresh, fresh2 or Express file exactly
or after removing whitespace is dropped and counted. Standard library only.
Writes corpus/project-<lang>/ and sets/project-<lang>.json.
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LITERALS = HERE.parent
OH = LITERALS / 'objective-holdout-v1'
sys.path.insert(0, str(OH))
import select_project as P  # noqa: E402

MIN_FILES = 40
MAX_FILES = 200


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--work', required=True)
    args = ap.parse_args()
    work = Path(args.work)
    work.mkdir(parents=True, exist_ok=True)
    seen_exact, seen_squeezed = set(), set()
    for spec, root in ((OH / 'frozen' / 'sets' / 'train.json', LITERALS),
                       (OH / 'frozen' / 'sets' / 'dev.json', LITERALS),
                       (OH / 'sets' / 'fresh.json', OH),
                       (OH / 'sets' / 'project.json', OH),
                       (HERE / 'sets' / 'fresh2.json', HERE)):
        for f in json.loads(spec.read_text())['files']:
            raw = (root / f['path']).read_bytes()
            seen_exact.add(P.sha256(raw))
            seen_squeezed.add(P.squeezed(raw))
    order = [r for r in P.order() if r != 'expressjs/express']
    for lang in ('python', 'javascript'):
        tried = []
        for repo in order:
            commit, version, licence, rlang, ext = P.CANDIDATES[repo]
            if rlang != lang:
                continue
            files, tar_sha = P.eligible_files(repo, work)
            tried.append({'repository': repo, 'commit': commit, 'tarball_sha256': tar_sha,
                          'eligible_files': len(files)})
            if len(files) < MIN_FILES:
                continue
            keep = sorted(files, key=lambda p: P.sha256((P.SEED + 'file:' + p).encode()))
            dropped = [p for p in keep if P.sha256(files[p]) in seen_exact or P.squeezed(files[p]) in seen_squeezed]
            keep = [p for p in keep if p not in set(dropped)][:MAX_FILES]
            out_dir = HERE / 'corpus' / f'project-{lang}'
            out_dir.mkdir(parents=True, exist_ok=True)
            recs = []
            for i, p in enumerate(sorted(keep)):
                raw = files[p]
                rel = f'corpus/project-{lang}/{i:04d}{ext}'
                (HERE / rel).write_bytes(raw)
                recs.append({'path': rel, 'unit': p, 'lang': lang, 'bytes': len(raw), 'sha256': P.sha256(raw),
                             'source_path': p})
            (HERE / 'sets').mkdir(exist_ok=True)
            (HERE / 'sets' / f'project-{lang}.json').write_text(json.dumps({
                'set': f'project-{lang}',
                'source': f'{repo} at {commit} ({version}), licence {licence}',
                'unit': 'source file',
                'selection': {'candidate_order': order, 'tried': tried, 'eligible_files': len(files),
                              'dropped_as_duplicates': dropped, 'kept': len(recs)},
                'files': recs,
            }, indent=1) + '\n')
            print(f'project-{lang}: {repo} at {commit[:12]}, {len(files)} eligible, {len(recs)} kept, '
                  f'{sum(r["bytes"] for r in recs)} bytes')
            break
        else:
            raise SystemExit(f'no {lang} candidate has {MIN_FILES} eligible files')


if __name__ == '__main__':
    main()
