#!/usr/bin/env python3
"""One entry point to check and reproduce this experiment. It changes nothing in the folder.

    python3 replay.py check     # seconds: integrity, split boundaries, a six-file end-to-end run
    python3 replay.py score     # about a minute: rescore all four sets and compare with the committed results
    python3 replay.py train     # about two minutes: retrain every dictionary and compare byte for byte
    python3 replay.py posthoc   # about two minutes: recompute the exploratory measurements made after scoring
    python3 replay.py all

Add --report FILE for a machine-readable record, --jobs N for workers. Exit status is 0 only if
every step passed. A step that could only be checked in part (no Git checkout, a different zstd
version) is printed as PART, never as PASS, and --strict turns it into a failure. `check` needs
Python 3 and zstd; `train` also needs a C compiler. None needs the network. Work happens in a
temporary directory that is removed afterwards.

Three files this script runs are frozen and cannot be repaired in place, so their known gaps are
closed here instead (see README.md, "Known limits of the frozen code"):
  train_arms.py does not read the engine's `stopped` flag and reuses a compiled engine it finds
    in its work directory. `train` gives it an empty work directory, a time bound, and then reads
    every chain's last line itself; `check` reads the frozen receipts for the same facts.
  The engine can spin forever when its pair table fills. `train` kills it after a bound.
  FORMAT.md tells a decoder to ignore padding, so independent_decode.py measures it and accepts
    it. `check` and `score` require less than one byte of padding, all zero, on every archive.

What each level is for:
  check  run it after any edit and before any freeze. It reruns no experiment.
  score  run it when the scorer, the format or a result file is in question.
  train  run it when the training code or the engine is in question.
  posthoc run it when explore_posthoc.py, explore_support.py or a number that comes from them is in question.
"""
import argparse
import hashlib
import json
import os
import shutil
import signal
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
TRAIN_TIMEOUT_SECONDS = 1800  # the frozen run took 98 s; four engine arms at their 300 s limit would take 1,200 s
STEP_TIMEOUT_SECONDS = 1800   # scoring one set takes under a minute; a worker that exits inside a pool blocks it forever
PROBLEMS_PER_SET = 200        # PREREGISTRATION.md: 200 problems, one Python and one JavaScript file each
ENGINE = LIT / 'fixed-source-v3' / 'engine.c'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def squeezed(raw):
    return sha256(b''.join(raw.split()))


class Part(str):
    """The result of a step that held as far as it could be checked, with part of it not checked.
    It must never read as a plain PASS."""


class Report:
    def __init__(self, strict=False):
        self.steps = []
        self.strict = strict

    def step(self, name, fn):
        t0 = time.perf_counter()
        try:
            detail = fn()
            status = 'PART' if isinstance(detail, Part) else 'PASS'
        except Exception as exc:  # a failed check is a result, not a crash
            detail = f'{type(exc).__name__}: {exc}'
            status = 'FAIL'
        seconds = round(time.perf_counter() - t0, 2)
        ok = status == 'PASS' or (status == 'PART' and not self.strict)
        self.steps.append({'step': name, 'status': status, 'ok': ok, 'seconds': seconds, 'detail': str(detail)})
        print(f'{status}  {name:28s} {seconds:7.2f}s  {detail}', flush=True)
        return ok

    @property
    def ok(self):
        return all(s['ok'] for s in self.steps)

    @property
    def partial(self):
        return [s['step'] for s in self.steps if s['status'] == 'PART']


def need(cond, message):
    if not cond:
        raise AssertionError(message)


def run_bounded(cmd, cwd, what, seconds=STEP_TIMEOUT_SECONDS):
    """Run a step in its own session and kill the whole session when it does not return: the frozen
    scorer raises SystemExit inside pool workers, and a pool whose worker exits waits forever."""
    proc = subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        log, _ = proc.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise AssertionError(f'{what} did not finish in {seconds} s and was killed')
    need(proc.returncode == 0, f'{what} failed: {log.strip()[-300:]}')
    return log


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
        return Part('NOT CHECKED: this is not a Git checkout, so whether Git tracks the frozen files is unknown')
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
    # Completeness, not only order: a set with problems quietly removed must not pass.
    for name in ('train', 'dev', 'fresh'):
        need(len(units[name]) == PROBLEMS_PER_SET, f'{name} has {len(units[name])} problems, not {PROBLEMS_PER_SET}')
        langs = {}
        for f in specs[name][0]['files']:
            langs.setdefault(f['unit'], []).append(f['lang'])
        odd = [u for u, ls in langs.items() if sorted(ls) != ['javascript', 'python']]
        need(not odd, f'{name}: problems without exactly one Python and one JavaScript file: {odd[:5]}')
    sel = specs['fresh'][0]['selection']
    taken = {f['rank'] for f in specs['fresh'][0]['files']}
    passed_over = {s['rank'] for s in sel['skipped']}
    need(not taken & passed_over and taken | passed_over == set(range(sel['first_rank'], sel['last_rank'] + 1)),
         'the fresh problems and the listed skips do not account for every rank from the first to the last')
    need(sel['first_rank'] == 2 * PROBLEMS_PER_SET, 'the fresh ranks do not start where the earlier problems end')
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


def decode_sound(name, results_path, decode_path, manifest_path):
    """Read every verdict the independent decoder wrote, not only how many archives it lists.
    FORMAT.md lets a decoder ignore padding; a verifier must not, or junk after the last file passes."""
    raw = results_path.read_bytes()
    res, dec = json.loads(raw), json.loads(decode_path.read_text())
    need(res['set_manifest_sha256'] == sha256(manifest_path.read_bytes()), f'{name}: results were made from a different set manifest')
    need(dec['set_manifest_sha256'] == res['set_manifest_sha256'], f'{name}: decoder read a different set manifest')
    need(dec['compared_with_sha256'] == sha256(raw), f'{name}: the decoder compared itself with a different results file')
    need(dec['all_ok'] is True and not dec['failures'], f'{name}: the decoder reports failures: {dec["failures"][:3]}')
    need(dec['source_files_match_manifest_sha256_and_size'] is True, f'{name}: source files did not match the manifest when decoded')
    for key in ('archives_without_a_results_row', 'results_rows_without_an_archive', 'frozen_headers_without_an_archive'):
        need(not dec[key], f'{name}: {key.replace("_", " ")}: {dec[key][:3]}')
    need(sorted(res['headers']) == sorted(dec['headers']) and dec['archives'] == len(dec['headers']), f'{name}: scorer and decoder list different archives')
    need(dec['manifest_files'] == res['files'] and dec['source_bytes'] == res['source_bytes'], f'{name}: scorer and decoder saw different files')
    for h, r in res['headers'].items():
        d = dec['headers'][h]
        need(d['ok'] is True and d['all_files_equal'] is True and d['files_differing_from_source'] == 0 and d['files_equal_to_source'] == res['files'],
             f'{name}/{h}: decoder did not reproduce every file')
        need(d['begins_with_frozen_header'] and d['frozen_file_is_exactly_the_header'] and d['file_count_equals_manifest'],
             f'{name}/{h}: archive does not begin with the frozen header, or its file count is wrong')
        need(d['padding_bits'] < 8 and d['padding_all_zero'] is True,
             f'{name}/{h}: {d["padding_bits"]} bits follow the last file (the format pads with zero bits to one byte)')
        count_bytes = max(1, (d['files'].bit_length() + 6) // 7)  # the file count is a varint between header and payload
        need(d['header_bytes'] + count_bytes + d['payload_bytes'] == d['archive_bytes'], f'{name}/{h}: header, file count and payload do not add up to the archive')
        need(d['payload_bits_used'] + d['padding_bits'] == 8 * d['payload_bytes'], f'{name}/{h}: used and padding bits do not add up to the payload')
        need(d['archive_bytes'] == r['bytes']['complete'] and d['archive_sha256'] == r['archive_sha256'], f'{name}/{h}: archive differs')
        need(d['tokens'] == r['bit_parse_tokens'] and d['escapes'] == r['escapes_in_bit_parse'], f'{name}/{h}: counts differ')
    return len(res['headers'])


def scorer_files_pinned():
    """The scorer logged the SHA-256 of every file it brought back. Nothing else pins the test sets,
    the results or the decoder, so read that list and hold the files to it."""
    text = (HERE / 'SCORER-LOG.md').read_text()
    block = text.split('## SHA-256 of the files brought back', 1)
    need(len(block) == 2, 'SCORER-LOG.md has no list of the files brought back')
    pinned = [line.split() for line in block[1].split('```')[1].strip().splitlines()]
    need(len(pinned) >= 19 and all(len(p) == 2 and len(p[0]) == 64 for p in pinned), 'the list in SCORER-LOG.md is not hashes and paths')
    for digest, rel in pinned:
        need((HERE / rel).exists() and sha256((HERE / rel).read_bytes()) == digest, f'{rel} is not the file the scorer brought back')
    wanted = {f'out/{kind}-{name}.{ext}' for name in SETS for kind, ext in (('results', 'json'), ('decode', 'json'), ('entries', 'json'), ('per-file', 'csv'))}
    wanted |= {'sets/fresh.json', 'sets/project.json', 'independent_decode.py'}
    need(wanted <= {rel for _, rel in pinned}, f'the scorer\'s list does not cover {sorted(wanted - {rel for _, rel in pinned})}')
    return f'{len(pinned)} files (both test-set manifests, results, decoder reports, the decoder itself) are the ones the scorer logged'


def near_duplicate_receipt():
    """The frozen selector skipped no problem as a Python near-duplicate. That is only evidence if it
    could have: the receipt must show earlier submissions were found in IBM's clusters."""
    path = HERE / 'out' / 'near-duplicate-audit.json'
    need(path.exists(), 'out/near-duplicate-audit.json is missing; run audit_near_duplicates.py where IBM\'s cluster file is')
    a = json.loads(path.read_text())
    spec, _ = load_set('fresh')
    fresh = sorted(f['s_id'] for f in spec['files'] if f['lang'] == 'python')
    need(a['clusters_file_sha256'] == spec['selection']['python_near_duplicate_clusters_sha256'], 'the audit read a different cluster file from the selection')
    need(a['unseen_python_submissions_sha256'] == sha256('\n'.join(fresh).encode()), 'the audit was made for a different set of unseen submissions')
    need(a['clusters'] > 0 and a['of_those_shaped_like_a_submission_id'] >= 0.999 * a['submissions_in_clusters'], 'the cluster file did not parse into submission ids')
    need(a['earlier_python_submissions_found_in_a_cluster'] > 0 and a['clusters_with_an_earlier_submission'] > 0,
         'no earlier submission was found in any cluster, so the near-duplicate filter could not have excluded anything')
    need(a['unseen_python_submissions_in_a_cluster_with_an_earlier_one'] == [], 'an unseen Python submission is in a near-duplicate cluster with an earlier one')
    return (f'{a["clusters"]:,} IBM clusters parsed; {a["earlier_python_submissions_found_in_a_cluster"]} of {a["earlier_python_submissions"]} earlier Python '
            f'submissions are in one, with {a["other_submissions_in_those_clusters"]:,} near-duplicates between them; none of the {a["unseen_python_submissions"]} unseen ones is among those')


def results_consistent():
    archives = sum(decode_sound(name, HERE / 'out' / f'results-{name}.json', HERE / 'out' / f'decode-{name}.json', SETS[name][0]) for name in SETS)
    return (f'{archives} archives: every decoder verdict is true, padding is under a byte and zero, and decoder and scorer '
            f'agree on bytes, hashes, tokens and escapes')


def frozen_training_complete():
    """The frozen trainer cannot be edited, so read its receipts: no engine arm may have reached its time
    limit or returned a short chain, and the engine source must be the one the receipts name."""
    summary = json.loads((HERE / 'frozen' / 'train-summary.json').read_text())
    eng = summary['engine']
    need(sha256(ENGINE.read_bytes()) == eng['source_sha256'], 'fixed-source-v3/engine.c is not the source the frozen run recorded')
    slow = {k: v for k, v in eng['seconds'].items() if v >= eng['limit_seconds']}
    need(not slow, f'an engine arm reached its {eng["limit_seconds"]} s limit in the frozen run: {slow}')
    need(all(v is True for v in eng['matches_earlier_chain'].values()), 'a frozen chain differed from the chain an earlier build produced')
    full = eng['kmax'] - summary['singleton_bytes']
    arms = 0
    for line in (HERE / 'frozen' / 'train.log').read_text().splitlines():
        if line.startswith('engine '):
            mode, count = line.split(':')[0].split()[1], int(line.split(':')[1].split()[0])
            need(count == full, f'engine {mode} returned {count} fragments in the frozen run, not the {full} it was asked for')
            arms += 1
    need(arms == len(eng['seconds']), 'the frozen log does not show every engine arm')
    filled = 0
    for name, h in summary['headers'].items():
        if h['variant'] == 'base' and h['arm'] in ('bpe', 'freq', 'length', 'token'):
            need(h['slots_used_with_escape'] == h['cap'], f'{name} does not fill its cap')
            filled += 1
        need(h['slots_used_with_escape'] <= h['cap'], f'{name} exceeds its cap')
    return (f'{arms} engine arms returned all {full} fragments, the slowest in {max(eng["seconds"].values())} s of a {eng["limit_seconds"]} s limit; '
            f'{filled} fixed-size dictionaries fill their caps; engine.c is the recorded source')


def results_md(tmp):
    work = tmp / 'results-md'
    work.mkdir()
    done = subprocess.run([sys.executable, 'make_results.py', '--out', str(work)], cwd=HERE, capture_output=True, text=True)
    need(done.returncode == 0, 'make_results.py refused to write: ' + (done.stderr or done.stdout).strip()[-300:])
    need((work / 'RESULTS.md').read_bytes() == (HERE / 'RESULTS.md').read_bytes(), 'RESULTS.md is not what make_results.py produces from out/')
    need((work / 'rule-outcomes.json').read_bytes() == (HERE / 'out' / 'rule-outcomes.json').read_bytes(),
         'out/rule-outcomes.json is not what make_results.py produces from out/')
    rules = json.loads((work / 'rule-outcomes.json').read_text())['rules']
    return ('RESULTS.md and out/rule-outcomes.json regenerate byte for byte; every guarded sentence still holds; '
            + ' '.join(f'{k}={"holds" if v["holds"] else "fails"}' for k, v in rules.items()))


def guards_bite():
    """A check that cannot fail proves nothing: break receipts on purpose and require a refusal."""
    done = subprocess.run([sys.executable, 'test_replay.py'], cwd=HERE, capture_output=True, text=True)
    lines = [line for line in done.stdout.strip().splitlines() if not line.startswith(('PASS', 'PART', 'FAIL  probe'))]
    need(done.returncode == 0, 'a guard let a broken receipt through: ' + ' | '.join(lines)[-400:])
    return lines[-1]


def tiny_fixture(tmp, jobs):
    """Format tests on hand-made inputs, then six real training files and one made-up file through
    the frozen scorer and the independent decoder. Fast enough to run after every edit.

    No file in any real set needs the escape, so on the real sets "the escape counts agree" is 0 = 0
    and the decoder's escape branch never runs. The made-up file holds three byte values that occur
    in no training file, which only the escape can code."""
    # The format tests read no data files, so they run without isolation and can import their neighbour.
    subprocess.run([sys.executable, 'test_bits_oh.py'], cwd=HERE, check=True, capture_output=True)
    spec, _ = load_set('train')
    alphabet = set()
    for f in spec['files']:
        alphabet.update((LIT / f['path']).read_bytes())
    absent = bytes(b for b in range(256) if b not in alphabet)[:3]
    need(len(absent) == 3, 'every byte value occurs in training; the escape cannot be exercised')
    out = tmp / 'tiny'
    root = tmp / 'tiny-root'
    out.mkdir()
    root.mkdir()
    files = []
    for f in [f for f in spec['files'] if f['lang'] == 'python'][:3] + [f for f in spec['files'] if f['lang'] == 'javascript'][:3]:
        shutil.copy(LIT / f['path'], root / Path(f['path']).name)
        files.append(dict(f, path=Path(f['path']).name))
    made_up = b'# a file with three bytes no training file contains: ' + absent[:1] + b' and ' + absent[1:2] + b' and ' + absent[2:3] + b'\nprint(input())\n'
    (root / 'escape.py').write_bytes(made_up)
    files.append({'path': 'escape.py', 'unit': 'made-up', 'lang': 'python', 'bytes': len(made_up), 'sha256': sha256(made_up)})
    manifest = out / 'tiny.json'
    manifest.write_text(json.dumps({'set': 'tiny', 'files': files}))
    run_bounded([sys.executable, '-I', 'score.py', '--set', str(manifest), '--root', str(root), '--out', str(out), '--jobs', str(min(jobs, 4))],
                HERE, 'the frozen scorer on the fixture')
    done = subprocess.run([sys.executable, '-I', 'independent_decode.py', '--set', str(manifest), '--root', str(root), '--out', str(out),
                           '--frozen', str(HERE / 'frozen')], cwd=HERE, capture_output=True, text=True)
    need(done.returncode == 0, 'independent decoder failed on the fixture: ' + done.stdout[-300:])
    n = decode_sound('tiny', out / 'results-tiny.json', out / 'decode-tiny.json', manifest)
    headers = json.loads((out / 'results-tiny.json').read_text())['headers']
    wrong = {h: r['escapes_in_bit_parse'] for h, r in headers.items() if r['escapes_in_bit_parse'] != len(absent)}
    need(not wrong, f'each archive must escape exactly the {len(absent)} unknown bytes: {wrong}')
    return (f'format tests pass; {len(files)} files x {n} dictionaries encoded and independently decoded, '
            f'{len(absent)} escaped bytes in each archive')


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
    run_bounded([sys.executable, '-I', 'score.py', '--set', str(manifest), '--root', str(root), '--out', str(out), '--jobs', str(jobs)],
                HERE, f'the frozen scorer on {name}')
    done = subprocess.run([sys.executable, '-I', 'independent_decode.py', '--set', str(manifest), '--root', str(root), '--out', str(out),
                           '--frozen', str(HERE / 'frozen')], cwd=HERE, capture_output=True, text=True)
    need(done.returncode == 0, f'independent decoder failed: {done.stdout[-300:]}')
    decode_sound(name, out / f'results-{name}.json', out / f'decode-{name}.json', manifest)
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
    text = (f'{len(h)} dictionaries on {old["files"]} files reproduce the committed results exactly{note}; '
            f'e.g. token gain at 4,096: {h["token-K4096"]["min_tokens"]:,} tokens, {h["token-K4096"]["bytes"]["complete"]:,} bytes')
    return Part(text) if note else text


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
    work = tmp / 'train' / 'work'  # new and empty, so train_arms.py compiles the engine from the source it then hashes
    need(not work.exists(), 'the training work directory already exists')
    # Its own session, so that a spinning engine dies with the trainer when the bound is reached.
    proc = subprocess.Popen([sys.executable, 'train_arms.py', '--work', str(work), '--jobs', str(jobs)], cwd=exp,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    try:
        log, _ = proc.communicate(timeout=TRAIN_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.communicate()
        raise AssertionError(f'training did not finish in {TRAIN_TIMEOUT_SECONDS} s and was killed; the engine cannot stop itself once its pair table is full')
    need(proc.returncode == 0, 'train_arms.py failed: ' + log.strip()[-300:])
    old_summary = json.loads((HERE / 'frozen' / 'train-summary.json').read_text())
    new_summary = json.loads((exp / 'frozen' / 'train-summary.json').read_text())
    need(new_summary['engine']['source_sha256'] == old_summary['engine']['source_sha256'], 'engine.c is not the source the frozen run recorded')
    chains = sorted((work / 'chains').glob('*.txt'))
    need(len(chains) == len(old_summary['engine']['seconds']), 'the retrain did not leave one chain per engine arm')
    asked = old_summary['engine']['kmax']
    for chain in chains:
        lines = chain.read_text().splitlines()
        last = lines[-1].split() if lines else []
        need(last[:1] == ['D'] and 'stopped=0' in last, f'{chain.name}: the engine did not finish inside its time limit, so the chain is short')
        got = sum(1 for line in lines if line.startswith('E '))
        need(got == asked, f'{chain.name}: {got} entries, not the {asked} asked for')
    same = 0
    skipped = ''
    for path in sorted((HERE / 'frozen').glob('*.boh')) + [HERE / 'frozen' / 'zstd-train-8k.dict']:
        new = exp / 'frozen' / path.name
        if path.suffix == '.dict':
            if old_summary['zstd']['version'] != new_summary['zstd']['version']:
                skipped = f' (zstd dictionary NOT compared: this machine has {new_summary["zstd"]["version"]})'
                continue
        need(new.exists() and new.read_bytes() == path.read_bytes(), f'{path.name} was not reproduced byte for byte')
        same += 1
    for name in ('train', 'dev'):
        need((exp / 'frozen' / 'sets' / f'{name}.json').read_bytes() == (HERE / 'frozen' / 'sets' / f'{name}.json').read_bytes(), f'set manifest {name} differs')
    # The summary carries what the dictionaries do not: which problems used each fragment, and the
    # training curve the byte-selected rule stopped on. Compare all of it except the clock.
    a, b = strip_timing(old_summary), strip_timing(new_summary)
    for summary in (a, b):  # set only when the trainer is given earlier chains to compare with, as the frozen run was
        summary['engine'].pop('matches_earlier_chain', None)
    if skipped:
        a['zstd'] = b['zstd'] = None
    differing = sorted(k for k in a if a[k] != b.get(k))
    if differing == ['engine']:
        differing = ['engine.' + k for k in a['engine'] if a['engine'][k] != b['engine'].get(k)]
    need(a == b, 'train-summary.json differs from the frozen one outside its timings: ' + ', '.join(differing)[:200])
    text = (f'{same} frozen files (dictionaries with code tables, zstd dictionary) retrained byte for byte from the training files; '
            f'{len(chains)} engine chains complete with {asked} entries each{skipped}')
    return Part(text) if skipped else text


# ---- posthoc -------------------------------------------------------------

def reexplore(script, committed, tmp, jobs):
    """The measurements made after scoring are not frozen, but the paper quotes them: recompute and compare."""
    target = tmp / committed
    cmd = [sys.executable, script, '--out', str(target)] + (['--jobs', str(jobs)] if script == 'explore_posthoc.py' else [])
    run_bounded(cmd, HERE, script)
    new, old = json.loads(target.read_text()), json.loads((HERE / 'out' / committed).read_text())
    note = ''
    lean = 'zstd_lean_framing'
    if lean in old and (lean not in new or new[lean]['version'] != old[lean]['version']):
        note = f' (zstd lean frames NOT compared: this machine has {new.get(lean, {}).get("version", "no zstd")})'
        new[lean] = old[lean] = None
    need(new == old, f'out/{committed} is not what {script} computes: ' + ', '.join(sorted(k for k in old if old[k] != new.get(k)))[:200])
    text = f'out/{committed} recomputed and equal in all {len(old)} sections{note}'
    return Part(text) if note else text


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('level', choices=('check', 'score', 'train', 'posthoc', 'all'))
    ap.add_argument('--jobs', type=int, default=min(8, os.cpu_count() or 1))
    ap.add_argument('--report')
    ap.add_argument('--strict', action='store_true', help='count a step that could only be checked in part as a failure')
    args = ap.parse_args()
    report = Report(strict=args.strict)
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='objective-holdout-replay-') as td:
        tmp = Path(td)
        if args.level in ('check', 'all'):
            report.step('frozen checksums', frozen_checksums)
            report.step('frozen files tracked by Git', frozen_tracked)
            report.step('sets match corpus', sets_match_corpus)
            report.step('split integrity', split_integrity)
            report.step('near-duplicate filter was live', near_duplicate_receipt)
            report.step('scorer files unchanged', scorer_files_pinned)
            report.step('scorer and decoder agree', results_consistent)
            report.step('frozen training was complete', frozen_training_complete)
            report.step('RESULTS.md regenerates', lambda: results_md(tmp))
            report.step('checks reject broken receipts', guards_bite)
            report.step('six-file end-to-end fixture', lambda: tiny_fixture(tmp, args.jobs))
        if args.level in ('score', 'all'):
            for name in SETS:
                report.step(f'rescore {name}', lambda name=name: rescore(name, tmp, args.jobs))
        if args.level in ('train', 'all'):
            report.step('retrain', lambda: retrain(tmp, args.jobs))
        if args.level in ('posthoc', 'all'):
            report.step('post hoc measurements', lambda: reexplore('explore_posthoc.py', 'posthoc-exploration.json', tmp, args.jobs))
            report.step('post hoc ranking scores', lambda: reexplore('explore_support.py', 'support-exploration.json', tmp, args.jobs))
    total = round(time.perf_counter() - t0, 2)
    if not report.ok:
        verdict = 'FAILED'
    elif report.partial:
        verdict = f'PASSED IN PART ({len(report.partial)} step(s) not fully checked: {", ".join(report.partial)})'
    else:
        verdict = 'ALL PASSED'
    print(f'{verdict} in {total}s')
    if args.report:
        Path(args.report).write_text(json.dumps({'schema': 'gamma.bits-objective-holdout.replay.v2', 'level': args.level, 'ok': report.ok,
                                                'partial': report.partial, 'seconds': total, 'steps': report.steps}, indent=1) + '\n')
    return 0 if report.ok else 1


if __name__ == '__main__':
    sys.exit(main())
