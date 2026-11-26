#!/usr/bin/env python3
"""One entry point to check and reproduce this experiment. It changes nothing in the folder.

    python3 replay.py check     # seconds: integrity, split boundaries, a six-file end-to-end run
    python3 replay.py score     # about a minute: rescore all four sets and compare with the committed results
    python3 replay.py train     # about two minutes: retrain every dictionary and compare byte for byte
    python3 replay.py all

Add --report FILE for a machine-readable record, --jobs N for workers. Exit status is 0 only if
every step passed. `check` needs Python 3 and zstd; `train` also needs a C compiler. None needs
the network. Work happens in a temporary directory that is removed afterwards.

What each level is for:
  check  run it after any edit and before any freeze. It reruns no experiment.
  score  run it when the scorer, the format or a result file is in question.
  train  run it when the training code or the engine is in question.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent
SETS = {  # name -> (manifest, directory its paths are relative to)
    'train': (HERE / 'frozen' / 'sets' / 'train.json', LIT),
    'dev': (HERE / 'frozen' / 'sets' / 'dev.json', LIT),
    'fresh': (HERE / 'sets' / 'fresh.json', HERE),
    'project': (HERE / 'sets' / 'project.json', HERE),
}
RANK_SEED = 'bits-codenet-replication-v1:'
TIMING_KEYS = {'seconds'}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def squeezed(raw):
    return sha256(b''.join(raw.split()))


class Report:
    def __init__(self):
        self.steps = []

    def step(self, name, fn):
        t0 = time.perf_counter()
        try:
            detail = fn()
            ok = True
        except Exception as exc:  # a failed check is a result, not a crash
            detail = f'{type(exc).__name__}: {exc}'
            ok = False
        seconds = round(time.perf_counter() - t0, 2)
        self.steps.append({'step': name, 'ok': ok, 'seconds': seconds, 'detail': detail})
        print(f'{"PASS" if ok else "FAIL"}  {name:28s} {seconds:7.2f}s  {detail}', flush=True)
        return ok

    @property
    def ok(self):
        return all(s['ok'] for s in self.steps)


def need(cond, message):
    if not cond:
        raise AssertionError(message)


def load_set(name):
    manifest, root = SETS[name]
    spec = json.loads(manifest.read_text())
    return spec, root


# ---- check ---------------------------------------------------------------

def frozen_checksums():
    lines = (HERE / 'SHA256SUMS-FROZEN').read_text().splitlines()
    for line in lines:
        digest, rel = line.split(None, 1)
        path = HERE / rel.strip()
        need(path.exists(), f'{rel} is listed but missing')
        need(sha256(path.read_bytes()) == digest, f'{rel} does not match its frozen hash')
    return f'{len(lines)} frozen files match'


def frozen_tracked():
    """A freeze that lists a file Git ignores cannot be reproduced from a clone."""
    listed = [l.split(None, 1)[1].strip() for l in (HERE / 'SHA256SUMS-FROZEN').read_text().splitlines()]
    probe = subprocess.run(['git', '-C', str(HERE), 'rev-parse', '--is-inside-work-tree'], capture_output=True, text=True)
    if probe.returncode != 0:
        return 'not a Git checkout; skipped'
    tracked = set(subprocess.run(['git', '-C', str(HERE), 'ls-files'], capture_output=True, text=True, check=True).stdout.split('\n'))
    missing = [rel for rel in listed if rel not in tracked]
    need(not missing, f'listed in the freeze but not tracked by Git: {missing}')
    return f'{len(listed)} frozen files are tracked'


def sets_match_corpus():
    total = 0
    for name in SETS:
        spec, root = load_set(name)
        for f in spec['files']:
            raw = (root / f['path']).read_bytes()
            need(len(raw) == f['bytes'] and sha256(raw) == f['sha256'], f'{name}: {f["path"]} differs from its manifest')
            total += 1
    return f'{total} files match their manifests'


def split_integrity():
    specs = {name: load_set(name) for name in SETS}
    units = {name: {f['unit'] for f in specs[name][0]['files']} for name in ('train', 'dev', 'fresh')}
    for a, b in (('train', 'dev'), ('train', 'fresh'), ('dev', 'fresh')):
        need(not units[a] & units[b], f'{a} and {b} share problems: {sorted(units[a] & units[b])[:5]}')
    clusters = {}
    for line in (HERE / 'metadata' / 'ibm-identical-problem-clusters.txt').read_text().split():
        members = frozenset(line.split(','))
        for p in members:
            clusters[p] = members
    prior = units['train'] | units['dev']
    seen = set()
    for p in sorted(units['fresh']):
        mates = clusters.get(p, frozenset([p]))
        need(not mates & prior, f'fresh problem {p} is in an identical-problem cluster with a training or development problem')
        need(not mates & seen, f'fresh problem {p} shares a cluster with another fresh problem')
        seen |= mates
    for skip in specs['fresh'][0]['selection']['skipped']:
        if skip['reason'].startswith('identical-problem cluster'):
            need(clusters.get(skip['p_id'], frozenset()) & (prior | units['fresh']), f'skip of {skip["p_id"]} is not explained by the cluster file')
    key = lambda p: sha256((RANK_SEED + p).encode())
    need(max(map(key, prior)) < min(map(key, units['fresh'])), 'a fresh problem ranks before a training or development problem')
    ranked = sorted({(f['rank'], f['unit']) for f in specs['fresh'][0]['files']})
    need([u for _, u in ranked] == sorted(units['fresh'], key=key), 'fresh ranks do not follow the hash order')
    exact, loose = {}, {}
    for name in ('train', 'dev', 'fresh', 'project'):
        spec, root = specs[name]
        for f in spec['files']:
            raw = (root / f['path']).read_bytes()
            for table, digest in ((exact, sha256(raw)), (loose, squeezed(raw))):
                other = table.get(digest)
                need(other is None or other == name or {other, name} == {'train', 'dev'},
                     f'{name} file {f["path"]} duplicates a {other} file')
                table.setdefault(digest, name)
    known = sorted(tuple(sorted(c)) for c in set(clusters.values()) if c & units['train'] and c & units['dev'])
    return (f'{len(units["fresh"])} fresh problems: none shared, clustered or duplicated with training or development; '
            f'ranks after all {len(prior)} earlier problems. Known and reported: {len(known)} development problems are '
            f'IBM-identical to training problems')


def results_consistent():
    archives = 0
    for name in SETS:
        res = json.loads((HERE / 'out' / f'results-{name}.json').read_text())
        dec = json.loads((HERE / 'out' / f'decode-{name}.json').read_text())
        need(res['set_manifest_sha256'] == sha256(SETS[name][0].read_bytes()), f'{name}: results were made from a different set manifest')
        need(sorted(res['headers']) == sorted(dec['headers']), f'{name}: scorer and decoder list different archives')
        for h, r in res['headers'].items():
            d = dec['headers'][h]
            need(d['ok'] and d['all_files_equal'], f'{name}/{h}: decoder did not reproduce every file')
            need(d['archive_bytes'] == r['bytes']['complete'] and d['archive_sha256'] == r['archive_sha256'], f'{name}/{h}: archive differs')
            need(d['tokens'] == r['bit_parse_tokens'] and d['escapes'] == r['escapes_in_bit_parse'], f'{name}/{h}: counts differ')
            archives += 1
    return f'{archives} archives: independent decoder and scorer agree on bytes, hashes, tokens and escapes'


def results_md(tmp):
    work = tmp / 'results-md'
    (work / 'out').mkdir(parents=True)
    (work / 'sets').mkdir()
    shutil.copy(HERE / 'make_results.py', work)
    for p in (HERE / 'out').glob('*.json'):
        shutil.copy(p, work / 'out')
    for p in (HERE / 'sets').glob('*.json'):
        shutil.copy(p, work / 'sets')
    subprocess.run([sys.executable, 'make_results.py'], cwd=work, check=True, capture_output=True)
    need((work / 'RESULTS.md').read_bytes() == (HERE / 'RESULTS.md').read_bytes(), 'RESULTS.md is not what make_results.py produces from out/')
    return 'RESULTS.md regenerates byte for byte from out/'


def tiny_fixture(tmp, jobs):
    """Format tests on hand-made inputs, then six real training files through the frozen scorer
    and the independent decoder. Fast enough to run after every edit."""
    # The format tests read no data files, so they run without isolation and can import their neighbour.
    subprocess.run([sys.executable, 'test_bits_oh.py'], cwd=HERE, check=True, capture_output=True)
    spec, _ = load_set('train')
    files = [f for f in spec['files'] if f['lang'] == 'python'][:3] + [f for f in spec['files'] if f['lang'] == 'javascript'][:3]
    out = tmp / 'tiny'
    out.mkdir()
    manifest = out / 'tiny.json'
    manifest.write_text(json.dumps({'set': 'tiny', 'files': files}))
    subprocess.run([sys.executable, '-I', 'score.py', '--set', str(manifest), '--root', str(LIT), '--out', str(out), '--jobs', str(min(jobs, 4))],
                   cwd=HERE, check=True, capture_output=True)
    done = subprocess.run([sys.executable, '-I', 'independent_decode.py', '--set', str(manifest), '--root', str(LIT), '--out', str(out),
                           '--frozen', str(HERE / 'frozen')], cwd=HERE, capture_output=True, text=True)
    need(done.returncode == 0, 'independent decoder failed on the six-file fixture: ' + done.stdout[-300:])
    n = len(json.loads((out / 'results-tiny.json').read_text())['headers'])
    return f'format tests pass; {len(files)} files x {n} dictionaries encoded and independently decoded'


# ---- score ---------------------------------------------------------------

def strip_timing(obj):
    if isinstance(obj, dict):
        return {k: strip_timing(v) for k, v in obj.items() if k not in TIMING_KEYS}
    if isinstance(obj, list):
        return [strip_timing(v) for v in obj]
    return obj


def rescore(name, tmp, jobs):
    manifest, root = SETS[name]
    out = tmp / 'score'
    out.mkdir(exist_ok=True)
    subprocess.run([sys.executable, '-I', 'score.py', '--set', str(manifest), '--root', str(root), '--out', str(out), '--jobs', str(jobs)],
                   cwd=HERE, check=True, capture_output=True)
    done = subprocess.run([sys.executable, '-I', 'independent_decode.py', '--set', str(manifest), '--root', str(root), '--out', str(out),
                           '--frozen', str(HERE / 'frozen')], cwd=HERE, capture_output=True, text=True)
    need(done.returncode == 0, f'independent decoder failed: {done.stdout[-300:]}')
    new = strip_timing(json.loads((out / f'results-{name}.json').read_text()))
    old = strip_timing(json.loads((HERE / 'out' / f'results-{name}.json').read_text()))
    note = ''
    if new['zstd']['version'] != old['zstd']['version']:
        note = f' (zstd rows not compared: this machine has {new["zstd"]["version"]})'
        new['zstd'] = old['zstd'] = None
    need(new == old, f'results-{name}.json differs from the committed file')
    for other in (f'entries-{name}.json', f'per-file-{name}.csv'):
        need((out / other).read_bytes() == (HERE / 'out' / other).read_bytes(), f'{other} differs from the committed file')
    h = old['headers']
    return (f'{len(h)} dictionaries on {old["files"]} files reproduce the committed results exactly{note}; '
            f'e.g. token gain at 4,096: {h["token-K4096"]["min_tokens"]:,} tokens, {h["token-K4096"]["bytes"]["complete"]:,} bytes')


# ---- train ---------------------------------------------------------------

def retrain(tmp, jobs):
    need(shutil.which('cc') and shutil.which('zstd'), 'needs a C compiler and zstd')
    lit = tmp / 'train' / 'literals'
    exp = lit / 'objective-holdout-v1'
    exp.mkdir(parents=True)
    for name in ('train_arms.py', 'bits_oh.py'):
        shutil.copy(HERE / name, exp)
    (lit / 'fixed-source-v3').mkdir()
    shutil.copy(LIT / 'fixed-source-v3' / 'engine.c', lit / 'fixed-source-v3')
    (lit / 'codenet-replication-v1').mkdir()
    shutil.copy(LIT / 'codenet-replication-v1' / 'manifest.json', lit / 'codenet-replication-v1')
    os.symlink(LIT / 'codenet-replication-v1' / 'corpus', lit / 'codenet-replication-v1' / 'corpus')
    subprocess.run([sys.executable, 'train_arms.py', '--work', str(tmp / 'train' / 'work'), '--jobs', str(jobs)], cwd=exp, check=True, capture_output=True)
    same = 0
    for path in sorted((HERE / 'frozen').glob('*.boh')) + [HERE / 'frozen' / 'zstd-train-8k.dict']:
        new = exp / 'frozen' / path.name
        if path.suffix == '.dict':
            old_version = json.loads((HERE / 'frozen' / 'train-summary.json').read_text())['zstd']['version']
            new_version = json.loads((exp / 'frozen' / 'train-summary.json').read_text())['zstd']['version']
            if old_version != new_version:
                continue
        need(new.exists() and new.read_bytes() == path.read_bytes(), f'{path.name} was not reproduced byte for byte')
        same += 1
    for name in ('train', 'dev'):
        need((exp / 'frozen' / 'sets' / f'{name}.json').read_bytes() == (HERE / 'frozen' / 'sets' / f'{name}.json').read_bytes(), f'set manifest {name} differs')
    return f'{same} frozen files (dictionaries with code tables, zstd dictionary) retrained byte for byte from the training files'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('level', choices=('check', 'score', 'train', 'all'))
    ap.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument('--report')
    args = ap.parse_args()
    report = Report()
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='objective-holdout-replay-') as td:
        tmp = Path(td)
        if args.level in ('check', 'all'):
            report.step('frozen checksums', frozen_checksums)
            report.step('frozen files tracked by Git', frozen_tracked)
            report.step('sets match corpus', sets_match_corpus)
            report.step('split integrity', split_integrity)
            report.step('scorer and decoder agree', results_consistent)
            report.step('RESULTS.md regenerates', lambda: results_md(tmp))
            report.step('six-file end-to-end fixture', lambda: tiny_fixture(tmp, args.jobs))
        if args.level in ('score', 'all'):
            for name in SETS:
                report.step(f'rescore {name}', lambda name=name: rescore(name, tmp, args.jobs))
        if args.level in ('train', 'all'):
            report.step('retrain', lambda: retrain(tmp, args.jobs))
    total = round(time.perf_counter() - t0, 2)
    print(f'{"ALL PASSED" if report.ok else "FAILED"} in {total}s')
    if args.report:
        Path(args.report).write_text(json.dumps({'schema': 'gamma.bits-objective-holdout.replay.v1', 'level': args.level, 'ok': report.ok,
                                                'seconds': total, 'steps': report.steps}, indent=1) + '\n')
    return 0 if report.ok else 1


if __name__ == '__main__':
    sys.exit(main())
