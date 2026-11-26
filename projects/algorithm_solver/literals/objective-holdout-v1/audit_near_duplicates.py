#!/usr/bin/env python3
"""Did the Python near-duplicate filter see anything? A receipt, written after scoring (2026-11-26).

`select_fresh_codenet.py` (frozen) drops a candidate whose Python submission sits in one of IBM's
near-duplicate clusters together with an earlier submission. It dropped nothing for that reason.
It would also have dropped nothing had it misread the cluster file, so "0 dropped" proves nothing
alone. This script reads the file the way the frozen selector does and records what it found.

    python3 audit_near_duplicates.py --python-clusters /path/to/Project_CodeNet-Python.clusters

IBM's file (40 MB, Project CodeNet v1.0.0, derived/duplicates/Python) is not in this repository.
Writes out/near-duplicate-audit.json; `replay.py check` reads it.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--python-clusters', required=True)
    ap.add_argument('--out', default=str(HERE / 'out' / 'near-duplicate-audit.json'))
    args = ap.parse_args()
    raw = Path(args.python_clusters).read_bytes()
    manifest = json.loads((LIT / 'codenet-replication-v1' / 'manifest.json').read_text())
    prior = {pair['python']['s_id'] for split in ('primary', 'secondary') for pair in manifest['splits'][split]['pairs']}
    fresh_spec = json.loads((HERE / 'sets' / 'fresh.json').read_text())
    fresh = sorted(f['s_id'] for f in fresh_spec['files'] if f['lang'] == 'python')

    # The same reading as select_fresh_codenet.py: groups of lines separated by blank lines; the
    # submission id is the file name before its first dot, taken from the text before the first colon.
    clusters, group = [], []
    for line in raw.decode('utf-8', 'replace').splitlines():
        line = line.strip()
        if line:
            group.append(line.split(':', 1)[0].rsplit('/', 1)[-1].split('.', 1)[0])
        elif group:
            clusters.append(set(group))
            group = []
    if group:
        clusters.append(set(group))
    everyone = set().union(*clusters) if clusters else set()
    with_prior = [c for c in clusters if c & prior]
    near_prior = set().union(*with_prior) - prior if with_prior else set()
    looks_like_ids = sum(1 for x in everyone if len(x) == 10 and x[0] == 's' and x[1:].isdigit())
    out = {
        'schema': 'gamma.bits-objective-holdout.near-duplicate-audit.v1',
        'note': 'post hoc receipt; parses the IBM file as the frozen selector does',
        'clusters_file_sha256': hashlib.sha256(raw).hexdigest(),
        'clusters_file_bytes': len(raw),
        'sha256_recorded_by_the_selection': fresh_spec['selection']['python_near_duplicate_clusters_sha256'],
        'clusters': len(clusters),
        'submissions_in_clusters': len(everyone),
        'of_those_shaped_like_a_submission_id': looks_like_ids,
        'earlier_python_submissions': len(prior),
        'earlier_python_submissions_found_in_a_cluster': len(prior & everyone),
        'clusters_with_an_earlier_submission': len(with_prior),
        'other_submissions_in_those_clusters': len(near_prior),
        'unseen_python_submissions': len(fresh),
        'unseen_python_submissions_sha256': hashlib.sha256('\n'.join(fresh).encode()).hexdigest(),
        'unseen_python_submissions_found_in_a_cluster': len(set(fresh) & everyone),
        'unseen_python_submissions_in_a_cluster_with_an_earlier_one': sorted(set(fresh) & near_prior),
    }
    Path(args.out).write_text(json.dumps(out, indent=1) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
