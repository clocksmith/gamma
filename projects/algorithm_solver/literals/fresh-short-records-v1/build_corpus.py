#!/usr/bin/env python3
"""Deterministic builder for the fresh short-record workloads (fresh-short-records-v1).

The builder is public; its inputs are not. It reads everything that could reveal the test
split from the custody directory (outside the repository):

  sealed/candidates.json    candidate sources chosen by the custodian
  sealed/sources-full.json  accepted sources, each pinned to a commit (written by `finalize`)
  sealed/salt.hex           32 random bytes, generated once by `init-salt`

Steps, in order:

  pin        resolve each candidate to its current commit, fetch it anonymously, check the
             licence, extract the eligible records into a local cache
  finalize   write sealed/sources-full.json from the accepted pins
  init-salt  generate the salt (refuses to overwrite an existing one)
  build      split by source, cap each source, write release/ and sealed/ record files and
             the public manifest
  extract    re-fetch every pinned commit into a fresh cache (the rebuild path)
  verify     check the split, the hashes and that the public files carry no test data

Standard library only. Network access is anonymous `git` over HTTPS with credential helpers,
user configuration and prompts disabled.
"""
from __future__ import annotations

import argparse
import base64
import concurrent.futures
import fnmatch
import hashlib
import itertools
import json
import math
import os
import re
import shutil
import statistics
import subprocess
import sys
import time

SCHEMA = 'bits-fresh-short-records/v1'
CAP_PER_SOURCE = 150            # most records one source may contribute
MIN_DISTINCT_PER_SOURCE = 200   # a source with fewer distinct eligible records is not used
TEST_FRACTION = 0.25
VALIDATION_FRACTION = 0.25
SHARED_COLLECTION_FRACTION = 0.05   # two sources sharing this much are one collection

W1, W2, W3 = 'w1-short-files', 'w2-message-entries', 'w3-commit-subjects'
WORKLOADS = {
    W1: {
        'title': 'short source and config files',
        'record': 'the whole content of one file, byte for byte',
        'source_unit': 'repository',
        'kind': 'files',
        'min_len': 40,
        'max_len': 400,
        'extensions': ['.json', '.yml', '.yaml', '.toml', '.ts', '.tsx', '.js', '.jsx', '.mjs',
                       '.cjs', '.wgsl', '.glsl', '.vert', '.frag', '.css'],
        'skip_dirs': ['.git', '.yarn', '3rdparty', 'bower_components', 'build', 'deps', 'dist',
                      'ee', 'enterprise', 'external', 'externals', 'node_modules', 'out',
                      'target', 'third-party', 'third_party', 'thirdparty', 'vendor', 'vendors'],
    },
    W2: {
        'title': 'key-value message entries',
        'record': ('one entry of an English message catalogue: for JSON the pair "key": "value" '
                   'with nested keys joined by "."; for line formats (properties, ini, ftl, '
                   'strings, php) the stripped key=value line; for Android resources the '
                   'stripped <string name="...">...</string> line'),
        'source_unit': 'project',
        'kind': 'messages',
        'min_len': 40,
        'max_len': 1024,
        'max_paths': 40,
        'max_file_bytes': 8 * 1024 * 1024,
    },
    W3: {
        'title': 'commit subject lines',
        'record': 'the subject line of one non-merge commit',
        'source_unit': 'repository',
        'kind': 'commits',
        'min_len': 40,
        'max_len': 1024,
        'window_days': [10, 45, 180, 730, 2920],
        'window_min_commits': 700,
        'window': ('commits reachable from the pinned commit whose committer date is on or after '
                   '`since` (kept per source); `since` is the pinned commit date minus the first '
                   'window in window_days that holds at least window_min_commits non-merge commits, '
                   'or the longest window if none does'),
    },
}
ORDER = [W1, W2, W3]
SHORT = {W1: 'w1', W2: 'w2', W3: 'w3'}

GIT_BASE = ['git', '-c', 'credential.helper=', '-c', 'core.askPass=', '-c', 'protocol.version=2',
            '-c', 'http.userAgent=git/2.50.1', '-c', 'gc.auto=0']


class GitError(RuntimeError):
    pass


class Reject(RuntimeError):
    pass


# ---------------------------------------------------------------- small helpers

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_name(source: str) -> str:
    return re.sub(r'[^A-Za-z0-9._-]', '_', source.replace('/', '__'))


def read_json(path):
    with open(path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def write_json(path, obj, mode=None):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, indent=2, sort_keys=True, ensure_ascii=False)
        fh.write('\n')
    if mode is not None:
        os.chmod(tmp, mode)
    os.replace(tmp, path)


def length_stats(lengths):
    if not lengths:
        return {'min': 0, 'median': 0, 'mean': 0, 'p95': 0, 'max': 0}
    srt = sorted(lengths)
    p95 = srt[max(0, math.ceil(0.95 * len(srt)) - 1)]     # nearest-rank percentile
    return {'min': srt[0], 'median': statistics.median(srt),
            'mean': round(sum(srt) / len(srt), 2), 'p95': p95, 'max': srt[-1]}


def valid_record(rec: bytes, cfg) -> bool:
    if not (cfg['min_len'] <= len(rec) <= cfg['max_len']) or b'\x00' in rec:
        return False
    try:
        rec.decode('utf-8')
    except UnicodeDecodeError:
        return False
    return True


# ---------------------------------------------------------------- git plumbing

def git_env(work):
    home = os.path.join(work, 'home')
    tmp = os.path.join(work, 'tmp')
    os.makedirs(home, exist_ok=True)
    os.makedirs(tmp, exist_ok=True)
    # A minimal environment: no user or system git configuration, no credential helper,
    # no prompt, no on-demand object fetches.
    return {'PATH': os.environ.get('PATH', '/usr/bin:/bin'), 'HOME': home,
            'XDG_CONFIG_HOME': os.path.join(home, '.config'), 'TMPDIR': tmp,
            'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
            'GIT_TERMINAL_PROMPT': '0', 'GIT_ASKPASS': 'true', 'GIT_NO_LAZY_FETCH': '1',
            'LC_ALL': 'C'}


def git(env, args, cwd=None, data=None, timeout=1500):
    proc = subprocess.run(GIT_BASE + list(args), cwd=cwd, input=data, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=env, timeout=timeout)
    if proc.returncode != 0:
        tail = proc.stderr.decode('utf-8', 'replace').strip().replace('\n', ' | ')[-240:]
        raise GitError('git %s failed: %s' % (' '.join(args[:1]), tail))
    return proc.stdout


def resolve_head(env, url):
    out = git(env, ['ls-remote', url, 'HEAD'], timeout=120).decode()
    for line in out.splitlines():
        sha, _, ref = line.partition('\t')
        if ref == 'HEAD' and re.fullmatch(r'[0-9a-f]{40,64}', sha):
            return sha
    raise GitError('no HEAD advertised')


def init_repo(env, path, url):
    shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path)
    git(env, ['init', '-q', '.'], cwd=path)
    git(env, ['remote', 'add', 'origin', url], cwd=path)


def fetch_commit(env, path, sha, filt, depth=None, since=None):
    args = ['fetch', '-q', '--no-tags', '--filter=' + filt]
    args.append('--depth=%d' % depth if depth else '--shallow-since=%d' % since)
    git(env, args + ['origin', sha], cwd=path)


def fetch_objects(env, path, oids, filt):
    """Fetch named objects only (the request a partial clone would make on demand)."""
    oids = sorted(set(oids))
    if not oids:
        return
    git(env, ['-c', 'fetch.negotiationAlgorithm=noop', 'fetch', 'origin', '--no-tags',
              '--no-write-fetch-head', '--recurse-submodules=no', '--filter=' + filt, '--stdin'],
        cwd=path, data=('\n'.join(oids) + '\n').encode())


def commit_header(env, path, sha):
    head = git(env, ['cat-file', 'commit', sha], cwd=path).split(b'\n\n', 1)[0]
    text = head.decode('utf-8', 'replace')
    tree = re.search(r'^tree ([0-9a-f]{40,64})$', text, re.M).group(1)
    when = re.search(r'^committer .* (\d+) [+-]\d{4}$', text, re.M).group(1)
    return tree, int(when)


def ls_tree(env, path, treeish, recursive):
    out = git(env, ['ls-tree', '-z'] + (['-r'] if recursive else []) + [treeish], cwd=path)
    rows = []
    for ent in out.split(b'\0'):
        if not ent:
            continue
        meta, name = ent.split(b'\t', 1)
        mode, typ, oid = meta.decode().split(' ')
        rows.append((mode, typ, oid, name.decode('utf-8', 'surrogateescape')))
    return rows


def read_blobs(env, path, oids):
    """Return {oid: bytes} for the blobs that are present locally."""
    oids = sorted(set(oids))
    if not oids:
        return {}
    out = git(env, ['cat-file', '--batch'], cwd=path, data=('\n'.join(oids) + '\n').encode())
    res, pos = {}, 0
    while pos < len(out):
        nl = out.index(b'\n', pos)
        head = out[pos:nl].split(b' ')
        pos = nl + 1
        if len(head) != 3:              # "<oid> missing"
            continue
        size = int(head[2])
        if head[1] == b'blob':
            res[head[0].decode()] = out[pos:pos + size]
        pos += size + 1
    return res


# ---------------------------------------------------------------- licence check

LICENCE_FILE_RE = re.compile(
    r'^((mit|apache|bsd|gpl|lgpl|agpl|mpl)[-_.])?(licen[sc]e|copying|unlicense|copyright)([-_. ].*)?$', re.I)
LICENCE_DIR_RE = re.compile(r'^licen[sc]es?$', re.I)
OPEN_PATTERNS = [
    ('MIT', r'permission is hereby granted, free of charge, to any person obtaining a copy'),
    ('MIT', r'\bmit license\b'),
    ('MIT-0', r'mit no attribution'),
    ('Apache-2.0', r'apache license,? ?version 2\.0'),
    ('BSD', r'redistribution and use in source and binary forms'),
    ('ISC', r'permission to use, copy, modify,? and(/or)? distribute this software for any '
            r'purpose with or without fee is hereby granted'),
    ('MPL-2.0', r'mozilla public license,? ?(version|v\.?) ?2\.0'),
    ('EPL', r'eclipse public license'),
    ('Unlicense', r'this is free and unencumbered software released into the public domain'),
    ('CC0-1.0', r'cc0 1\.0 universal|creative commons zero'),
    ('CC-BY', r'creative commons attribution|attribution(-sharealike)? [34]\.0 (international|unported)'),
    ('BSL-1.0', r'boost software license'),
    ('PostgreSQL', r'permission to use, copy, modify, and distribute this software and its '
                   r'documentation for any purpose, without fee, and without a written agreement'),
    ('Zlib', r"this software is provided '?as-is'?, without any express or implied warranty"),
    ('OSL-3.0', r'open software license'),
    ('CDDL', r'common development and distribution license'),
    ('Artistic', r'artistic license'),
    ('PHP', r'the php license'),
    ('Ruby', r'2-clause bsdl'),
    ('EUPL', r'european union public licen[cs]e'),
    ('NCSA', r'university of illinois/ncsa open source license'),
    ('public-domain', r'the author disclaims copyright|dedicated to the public domain'),
    ('SPDX-pointer', r'spdx-license-identifier: ?\(?(gpl|lgpl|agpl|mit|apache|bsd|mpl|isc)'),
]
GNU_PATTERNS = [
    ('AGPL', r'gnu affero general public license'),
    ('LGPL', r'gnu (lesser|library) general public license'),
    ('GPL', r'gnu general public license'),
]
RESTRICTIVE_PATTERNS = [
    ('BUSL', r'business source license'), ('SSPL', r'server side public license'),
    ('Elastic', r'elastic license'), ('Commons-Clause', r'commons clause'),
    ('PolyForm', r'polyform'), ('Sustainable-Use', r'sustainable use license'),
    ('FSL', r'functional source license'), ('Fair-Source', r'fair source|fair-code'),
    ('Prosperity', r'prosperity public license'),
    ('CC-NC', r'attribution-noncommercial'),
    ('commercial-terms', r'commercial licen[cs]e|enterprise licen[cs]e|enterprise edition'),
]


def classify_licence(text):
    low = re.sub(r'\s+', ' ', text).lower().replace('‘', "'").replace('’', "'")
    found = []
    # GNU licence texts mention each other, so only the one named first counts.
    gnu = [(m.start(), name) for name, pat in GNU_PATTERNS for m in [re.search(pat, low)] if m]
    if gnu:
        pos, name = min(gnu)
        ver = re.search(r'version (\d(\.\d)?)', low[pos:pos + 160])
        found.append(name + ('-' + ver.group(1) if ver else ''))
    for name, pat in OPEN_PATTERNS:
        if re.search(pat, low) and name not in found:
            found.append(name)
    if 'BSD' in found:
        found[found.index('BSD')] = 'BSD-3-Clause' if 'neither the name' in low else 'BSD-2-Clause'
    flags = [name for name, pat in RESTRICTIVE_PATTERNS if re.search(pat, low)]
    return found, flags


def licence_rows(env, path, root_rows, all_rows=None):
    """Licence files in the repository root, plus the files of a root LICENSE(S) directory."""
    picked = [(name, oid) for mode, typ, oid, name in root_rows
              if typ == 'blob' and mode in ('100644', '100755') and LICENCE_FILE_RE.match(name)]
    for mode, typ, oid, name in root_rows:
        if typ != 'tree' or not LICENCE_DIR_RE.match(name):
            continue
        if all_rows is None:                # commits-only fetch: get this one directory listing
            fetch_objects(env, path, [oid], 'tree:0')
            inner = ls_tree(env, path, oid, recursive=False)
        else:
            inner = [(m, t, o, n[len(name) + 1:]) for m, t, o, n in all_rows
                     if n.startswith(name + '/') and '/' not in n[len(name) + 1:]]
        picked += [(name + '/' + n, o) for m, t, o, n in inner if t == 'blob' and m in ('100644', '100755')]
    return sorted(picked)[:12]


def detect_licence(env, path, rows, cand):
    """Classify the licence files of a repository; raise Reject if none is open."""
    fetch_objects(env, path, [oid for _, oid in rows], 'blob:none')
    blobs = read_blobs(env, path, [oid for _, oid in rows])
    files, found, flags = [], [], []
    for name, oid in rows:
        body = blobs.get(oid)
        if body is None:
            continue
        got, bad = classify_licence(body.decode('utf-8', 'replace'))
        files.append({'path': name, 'sha256': sha256_hex(body), 'matches': got, 'flags': bad})
        found += [x for x in got if x not in found]
        flags += [x for x in bad if x not in flags]
    info = {'spdx': ' / '.join(found), 'files': files, 'flags': flags}
    if cand.get('licence_note'):
        info['custodian_note'] = cand['licence_note']
    if not found:
        raise Reject('no open licence recognised in the repository root')
    if flags and not cand.get('licence_note'):
        raise Reject('licence needs review: ' + ', '.join(flags))
    return info


# ---------------------------------------------------------------- extractors

def extract_files(env, path, rows, cfg):
    exts = set(cfg['extensions'])
    skip = set(cfg['skip_dirs'])
    oids = []
    for mode, typ, oid, name in rows:
        if typ != 'blob' or mode not in ('100644', '100755'):
            continue
        parts = name.split('/')
        if skip & {p.lower() for p in parts[:-1]}:
            continue
        if os.path.splitext(parts[-1])[1].lower() in exts:
            oids.append(oid)
    blobs = read_blobs(env, path, oids)     # only blobs under the size limit were fetched
    return {body for body in blobs.values() if valid_record(body, cfg)}


GENERIC_SKIP = {'node_modules', 'test', 'tests', '__tests__', 'fixtures', 'e2e', 'example',
                'examples', 'docs', 'doc', 'cypress', 'mock', 'mocks', '__mocks__', 'vendor',
                'third_party', 'androidtest', 'debug'}
GENERIC_RE = re.compile(
    r'(^|/)(_locales/en(_us)?/messages\.json'
    r'|(en|en[-_]us|en[-_]gb|en[-_]en|english)(\.i18n|\.client)?\.json'
    r'|(locales?|i18n|lang|langs|languages?|translations?|l10n|intl|messages|strings)'
    r'/(en|en[-_]us|en[-_]gb|english)/[^/]+\.json'
    r'|res/values/strings\.xml)$', re.I)


def discover_paths(all_paths, cand, cfg):
    """Pick the English catalogue files of a candidate (pin step only)."""
    pats = cand.get('paths') or []
    excl = re.compile(cand['exclude']) if cand.get('exclude') else None
    hits = [p for p in all_paths if any(fnmatch.fnmatchcase(p, pat) for pat in pats)]
    how = 'listed'
    if not hits:
        how = 'generic'
        hits = [p for p in all_paths
                if GENERIC_RE.search(p) and not (GENERIC_SKIP & {c.lower() for c in p.split('/')[:-1]})]
    if excl:
        hits = [p for p in hits if not excl.search(p)]
    hits = [p for p in hits if not ({'ee', 'enterprise'} & {c.lower() for c in p.split('/')[:-1]})]
    hits = sorted(set(hits), key=lambda p: sha256_hex(p.encode('utf-8', 'surrogateescape')))
    return sorted(hits[:cfg['max_paths']]), how


def decode_text(body: bytes) -> str:
    if body[:2] in (b'\xff\xfe', b'\xfe\xff'):
        return body.decode('utf-16', 'replace')
    try:
        return body.decode('utf-8-sig')
    except UnicodeDecodeError:
        return body.decode('latin-1')


def flatten_json(obj, prefix, out):
    if isinstance(obj, dict):
        for key, val in obj.items():
            flatten_json(val, prefix + '.' + str(key) if prefix else str(key), out)
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            flatten_json(val, prefix + '.' + str(idx) if prefix else str(idx), out)
    elif isinstance(obj, str) and obj.strip() and prefix:
        out.append((prefix, obj))


KV_RE = re.compile(r'^(\S[^=]{0,198}?)\s*=\s*(\S.*)$')
KV_COMMENT = ('#', '!', ';', '//', '/*', '*', '<', '[', '--')
XML_RE = re.compile(r'^<string\b[^>]*\bname="[^"]+"[^>]*>(.+)</string>$')


def entries_from_file(name, body):
    """Yield the message entries of one catalogue file as bytes."""
    text = decode_text(body)
    ext = os.path.splitext(name)[1].lower()
    if ext in ('.json', '.arb'):
        pairs = []
        flatten_json(json.loads(text), '', pairs)
        for key, val in pairs:
            yield (json.dumps(key, ensure_ascii=False) + ': ' + json.dumps(val, ensure_ascii=False))
    elif ext == '.xml':
        for line in text.splitlines():
            line = line.strip()
            if XML_RE.match(line) and 'translatable="false"' not in line:
                yield line
    else:
        continued = False
        for line in text.splitlines():
            ends_open = (len(line) - len(line.rstrip('\\'))) % 2 == 1
            was_continued, continued = continued, ends_open
            line = line.strip()
            if was_continued or ends_open or not line or line.startswith(KV_COMMENT):
                continue
            if KV_RE.match(line):
                yield line


def extract_messages(env, path, rows, paths, cfg):
    by_path = {name: oid for mode, typ, oid, name in rows if typ == 'blob'}
    missing = [p for p in paths if p not in by_path]
    if missing:
        raise Reject('catalogue file missing at the pinned commit')
    fetch_objects(env, path, [by_path[p] for p in paths], 'blob:none')
    blobs = read_blobs(env, path, [by_path[p] for p in paths])
    records = set()
    for name in paths:
        body = blobs.get(by_path[name])
        if body is None or len(body) > cfg['max_file_bytes']:
            continue
        try:
            for entry in entries_from_file(name, body):
                try:
                    rec = entry.encode('utf-8')
                except UnicodeEncodeError:
                    continue
                if valid_record(rec, cfg):
                    records.add(rec)
        except ValueError:
            continue                      # not parseable as its declared format
    return records


def extract_subjects(env, path, sha, cfg):
    out = git(env, ['log', '-z', '--no-merges', '--format=%s', sha], cwd=path)
    subjects = [s for s in out.split(b'\0') if s]
    return len(subjects), {s for s in subjects if valid_record(s, cfg)}


# ---------------------------------------------------------------- one source

def process_source(wl, cand, env, work, cache_dir):
    """Fetch one source and cache its eligible records. `cand` carries a commit when pinned."""
    cfg = WORKLOADS[wl]
    name = cand['source']
    url = cand.get('url') or 'https://github.com/' + name
    res = {'workload': wl, 'source': name, 'org': (cand.get('org') or name.split('/')[0]).lower(),
           'url': url, 'status': 'rejected', 'reason': '', 'params': dict(cand.get('params') or {})}
    repo = os.path.join(work, 'clones', SHORT[wl] + '--' + safe_name(name))
    try:
        sha = cand.get('commit') or resolve_head(env, url)
        res['commit'] = sha
        detail = {}
        if cfg['kind'] == 'commits':
            params = res['params']
            if 'since' not in params:
                init_repo(env, repo, url)
                fetch_commit(env, repo, sha, 'tree:0', depth=1)
                _, when = commit_header(env, repo, sha)
                for days in cfg['window_days']:
                    since = when - days * 86400
                    init_repo(env, repo, url)
                    fetch_commit(env, repo, sha, 'tree:0', since=since)
                    count = int(git(env, ['rev-list', '--count', '--no-merges', sha], cwd=repo))
                    if count >= cfg['window_min_commits']:
                        break
                params.update({'window_days': days, 'since': since})
            else:
                init_repo(env, repo, url)
                fetch_commit(env, repo, sha, 'tree:0', since=params['since'])
            tree, when = commit_header(env, repo, sha)
            fetch_objects(env, repo, [tree], 'tree:0')
            root_rows = ls_tree(env, repo, tree, recursive=False)
            licence = detect_licence(env, repo, licence_rows(env, repo, root_rows), cand)
            detail['non_merge_commits'], records = extract_subjects(env, repo, sha, cfg)
        else:
            init_repo(env, repo, url)
            filt = 'blob:limit=%d' % (cfg['max_len'] + 1) if cfg['kind'] == 'files' else 'blob:none'
            fetch_commit(env, repo, sha, filt, depth=1)
            _, when = commit_header(env, repo, sha)
            rows = ls_tree(env, repo, sha, recursive=True)
            licence = detect_licence(
                env, repo, licence_rows(env, repo, [r for r in rows if '/' not in r[3]], rows), cand)
            if cfg['kind'] == 'files':
                records = extract_files(env, repo, rows, cfg)
            else:
                params = res['params']
                if 'paths' not in params:
                    paths, how = discover_paths([r[3] for r in rows if r[1] == 'blob'], cand, cfg)
                    if not paths:
                        raise Reject('no English catalogue file found')
                    params['paths'] = paths
                    detail['paths_found_by'] = how
                records = extract_messages(env, repo, rows, params['paths'], cfg)
        res.update({'commit_time': when, 'licence': licence, 'eligible': len(records), 'detail': detail})
        if len(records) < MIN_DISTINCT_PER_SOURCE:
            raise Reject('only %d distinct eligible records (need %d)' % (len(records), MIN_DISTINCT_PER_SOURCE))
        os.makedirs(os.path.join(cache_dir, wl), exist_ok=True)
        write_json(os.path.join(cache_dir, wl, safe_name(name) + '.json'),
                   {'source': name, 'commit': sha,
                    'records_b64': sorted(base64.b64encode(r).decode() for r in records)})
        res['status'] = 'accepted'
    except Reject as exc:
        res['reason'] = str(exc)
    except (GitError, subprocess.TimeoutExpired, OSError, AttributeError) as exc:
        res['reason'] = 'fetch error: ' + str(exc)[:300]
    finally:
        shutil.rmtree(repo, ignore_errors=True)
    return res


def run_pool(tasks, jobs, label):
    """tasks: list of zero-argument callables returning a result dict."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futs = [pool.submit(t) for t in tasks]
        for done, fut in enumerate(concurrent.futures.as_completed(futs), 1):
            res = fut.result()
            results.append(res)
            print('[%s %d/%d] %s %s %s %s' % (label, done, len(futs), res['workload'], res['source'],
                                              res['status'], res.get('eligible', res['reason'])), flush=True)
    return results


# ---------------------------------------------------------------- commands

def sealed(custody, *parts):
    return os.path.join(custody, 'sealed', *parts)


def cmd_pin(args):
    cands = read_json(sealed(args.custody, 'candidates.json'))
    orgs = {}
    for wl in ORDER:
        for cand in cands.get(wl, []):
            org = (cand.get('org') or cand['source'].split('/')[0]).lower()
            if org in orgs:
                sys.exit('organisation listed twice: %s (%s and %s)' % (org, orgs[org], cand['source']))
            orgs[org] = cand['source']
    env = git_env(args.work)
    pin_dir = os.path.join(args.work, 'pins')
    tasks = []
    for wl in ORDER:
        if args.workload and wl != args.workload:
            continue
        os.makedirs(os.path.join(pin_dir, wl), exist_ok=True)
        for cand in cands.get(wl, []):
            out = os.path.join(pin_dir, wl, safe_name(cand['source']) + '.json')
            if args.only and cand['source'] not in args.only:
                continue
            if os.path.exists(out) and not (args.force or (args.only and cand['source'] in args.only)):
                continue

            def task(wl=wl, cand=cand, out=out):
                res = process_source(wl, cand, env, args.work, os.path.join(args.work, 'cache'))
                write_json(out, res)
                return res
            tasks.append(task)
    run_pool(tasks, args.jobs, 'pin')


def drop_shared_collections(wl, keep, cache_dir):
    """Two sources that share 5% or more of the smaller one's eligible records are treated as
    one collection (one copies the other, or both copy a third). The larger one is dropped."""
    recs = {s['source']: set(read_json(os.path.join(cache_dir, wl, safe_name(s['source']) + '.json'))['records_b64'])
            for s in keep}
    dropped = []
    while True:
        where = {}
        for name, rows in recs.items():
            for rec in rows:
                where.setdefault(rec, []).append(name)
        pairs = {}
        for names in where.values():
            for pair in itertools.combinations(sorted(names), 2):
                pairs[pair] = pairs.get(pair, 0) + 1
        over = [(count, a, b) for (a, b), count in pairs.items()
                if count >= SHARED_COLLECTION_FRACTION * min(len(recs[a]), len(recs[b]))]
        if not over:
            return dropped
        count, a, b = max(over)
        loser, other = (a, b) if (len(recs[a]), a) > (len(recs[b]), b) else (b, a)
        dropped.append({'source': loser, 'reason': 'shares %d eligible records with %s (%.1f%% of the smaller '
                        'source); the larger source of such a pair is dropped'
                        % (count, other, 100.0 * count / min(len(recs[a]), len(recs[b])))})
        del recs[loser]


def cmd_finalize(args):
    cands = read_json(sealed(args.custody, 'candidates.json'))
    pin_dir = os.path.join(args.work, 'pins')
    recheck = {}
    if args.recheck:                        # results of a later `extract` run from the pins
        recheck = {(r['workload'], r['source']): r for r in read_json(args.recheck)}
    full = {'schema': SCHEMA + '/sources-full', 'workloads': {}}
    rejected = {}
    for wl in ORDER:
        keep, drop = [], []
        for cand in cands.get(wl, []):
            path = os.path.join(pin_dir, wl, safe_name(cand['source']) + '.json')
            if cand.get('drop'):                # set aside by the custodian, with the reason
                drop.append({'source': cand['source'], 'reason': cand['drop']})
                continue
            if not os.path.exists(path):
                sys.exit('candidate not pinned yet: %s' % cand['source'])
            res = read_json(path)
            again = recheck.get((wl, cand['source']))
            if res['status'] == 'accepted' and again:
                if again['status'] != 'accepted' or again['commit'] != res['commit']:
                    res.update({'status': 'rejected', 'reason': 'on rebuild: ' + (again['reason'] or 'commit differs')})
                else:
                    res['licence'] = again['licence']
            if res['status'] == 'accepted':
                keep.append({k: res[k] for k in ('source', 'org', 'url', 'commit', 'commit_time',
                                                 'licence', 'params', 'eligible')})
            else:
                drop.append({'source': res['source'], 'reason': res['reason']})
        shared = drop_shared_collections(wl, keep, os.path.join(args.work, 'cache'))
        gone = {d['source'] for d in shared}
        keep = [s for s in keep if s['source'] not in gone]
        drop += shared
        full['workloads'][wl] = {'sources': sorted(keep, key=lambda s: s['source'])}
        rejected[wl] = sorted(drop, key=lambda s: s['source'])
        print('%s: %d accepted, %d rejected' % (wl, len(keep), len(drop)))
    write_json(sealed(args.custody, 'sources-full.json'), full, mode=0o600)
    write_json(sealed(args.custody, 'rejected.json'), rejected, mode=0o600)


def cmd_init_salt(args):
    path = sealed(args.custody, 'salt.hex')
    if os.path.exists(path):
        sys.exit('a salt already exists; it is generated once and never replaced')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as fh:
        fh.write(os.urandom(32).hex() + '\n')
    print('salt written')


def cmd_extract(args):
    full = read_json(sealed(args.custody, 'sources-full.json'))
    env = git_env(args.work)
    tasks = []
    for wl in ORDER:
        if args.workload and wl != args.workload:
            continue
        for src in full['workloads'][wl]['sources']:
            def task(wl=wl, src=src):
                res = process_source(wl, src, env, args.work, os.path.join(args.work, 'cache'))
                if res['status'] == 'accepted' and res['eligible'] != src['eligible']:
                    res.update({'status': 'rejected', 'reason': 'eligible count differs from the pin'})
                return res
            tasks.append(task)
    results = run_pool(tasks, args.jobs, 'extract')
    # Keep what this run found, so `finalize --recheck` can drop sources that no longer pass
    # and store the licence findings made by this version of the builder.
    write_json(os.path.join(args.work, 'extract-results.json'),
               [{k: r.get(k) for k in ('workload', 'source', 'status', 'reason', 'commit', 'licence', 'eligible')}
                for r in sorted(results, key=lambda r: (r['workload'], r['source']))])
    bad = [r for r in results if r['status'] != 'accepted']
    if bad:
        sys.exit('%d sources could not be rebuilt from their pins' % len(bad))
    print('all pinned sources extracted')


def load_salt(custody):
    with open(sealed(custody, 'salt.hex'), 'r', encoding='ascii') as fh:
        salt = bytes.fromhex(fh.read().strip())
    if len(salt) != 32:
        sys.exit('salt must be 32 bytes')
    return salt


def split_sources(names, salt):
    """Rank sources by sha256(salt + name); first half train, then validation, then test."""
    ranked = sorted(names, key=lambda n: sha256_hex(salt + n.encode('utf-8')))
    n_test = math.ceil(len(ranked) * TEST_FRACTION)
    n_val = math.ceil(len(ranked) * VALIDATION_FRACTION)
    n_train = len(ranked) - n_val - n_test
    return {'train': ranked[:n_train], 'validation': ranked[n_train:n_train + n_val],
            'test': ranked[n_train + n_val:]}


def select_records(wl, sources, cache_dir, salt):
    """Return {source: [records]} after cross-source de-duplication and the per-source cap."""
    recs = {}
    for src in sources:
        cache = read_json(os.path.join(cache_dir, wl, safe_name(src['source']) + '.json'))
        if cache['commit'] != src['commit']:
            sys.exit('cache for %s is not at the pinned commit' % wl)
        recs[src['source']] = [base64.b64decode(b) for b in cache['records_b64']]
    owner = {}
    for name, rows in recs.items():       # a record found in several sources stays in one
        for rec in rows:
            key = hashlib.sha256(name.encode('utf-8') + b'\x00' + rec).digest()
            if rec not in owner or key < owner[rec][0]:
                owner[rec] = (key, name)
    chosen = {}
    for name, rows in recs.items():
        mine = [r for r in rows if owner[r][1] == name]
        chosen[name] = sorted(mine, key=lambda r: hashlib.sha256(salt + r).digest())[:CAP_PER_SOURCE]
    return chosen


def write_jsonl(path, rows, mode):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    blob = b''.join(json.dumps(r, sort_keys=True, separators=(',', ':')).encode('ascii') + b'\n'
                    for r in rows)
    with open(path, 'wb') as fh:
        fh.write(blob)
    os.chmod(path, mode)
    return sha256_hex(blob)


def test_sources_digest(salt, names):
    return sha256_hex(salt + '\n'.join(sorted(names)).encode('utf-8'))


def public_rules(wl):
    cfg = WORKLOADS[wl]
    rules = {k: v for k, v in cfg.items() if k != 'kind'}
    rules.update({'cap_per_source': CAP_PER_SOURCE, 'min_distinct_per_source': MIN_DISTINCT_PER_SOURCE,
                  'record_filter': 'valid UTF-8, no NUL byte, length within min_len..max_len bytes',
                  'duplicates': ('one copy per source; a record found in several sources is kept only '
                                 'in the source with the smallest sha256(source name + 0x00 + record)'),
                  'shared_collections': ('two sources that share %d%% or more of the smaller one\'s eligible '
                                         'records count as one collection; the larger one is not used'
                                         % round(100 * SHARED_COLLECTION_FRACTION)),
                  'cap_choice': 'the records with the smallest sha256(salt + record)'})
    return rules


def cmd_build(args):
    out = args.out_custody or args.custody
    salt = load_salt(args.custody)
    full = read_json(sealed(args.custody, 'sources-full.json'))
    cache_dir = os.path.join(args.work, 'cache')
    manifest = {
        'schema': SCHEMA,
        'built_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'builder': {'file': 'build_corpus.py',
                    'sha256': sha256_hex(open(os.path.abspath(__file__), 'rb').read())},
        'split_rule': {
            'unit': 'source (one source per organisation, across all three workloads)',
            'order': 'sources sorted by sha256(salt + source name), hex ascending',
            'sizes': 'test = ceil(n/4) at the end, validation = ceil(n/4) before it, train = the rest',
            'salt': '32 random bytes, generated once, held in the custody directory',
        },
        'length_statistics': 'bytes per record; p95 is the nearest-rank percentile',
        'licence_field': ('licence names recognised in the licence files at the repository root (or in a '
                          'root LICENSE/LICENSES directory); a repository with several such files lists '
                          'every name found, so the list can include licences of bundled third-party code'),
        'test_sources_digest': 'sha256(salt + sorted test source names joined by a newline)',
        'workloads': {},
    }
    test_sources = {}
    seen_ids = set()
    for wl in ORDER:
        sources = full['workloads'][wl]['sources']
        by_name = {s['source']: s for s in sources}
        chosen = select_records(wl, sources, cache_dir, salt)
        split = split_sources(list(by_name), salt)
        entry = {'title': WORKLOADS[wl]['title'], 'rules': public_rules(wl),
                 'sources_total': len(sources), 'splits': {}}
        for part in ('train', 'validation', 'test'):
            rows, per_source, lengths = [], [], []
            for name in split[part]:
                recs = chosen[name]
                for rec in recs:
                    rid = SHORT[wl] + '-' + sha256_hex(name.encode('utf-8') + b'\x00' + rec)[:16]
                    if rid in seen_ids:
                        sys.exit('record id collision')
                    seen_ids.add(rid)
                    rows.append({'id': rid, 'source': name,
                                 'record_b64': base64.b64encode(rec).decode('ascii')})
                    lengths.append(len(rec))
                src = by_name[name]
                item = {'source': name, 'url': src['url'], 'commit': src['commit'],
                        'licence': src['licence']['spdx'], 'records': len(recs),
                        'bytes': sum(len(r) for r in recs)}
                if src['params']:
                    item['params'] = src['params']
                per_source.append(item)
            summary = {'sources': len(split[part]), 'records': len(rows),
                       'total_bytes': sum(lengths), 'record_length': length_stats(lengths)}
            if part == 'test':
                digest = write_jsonl(os.path.join(out, 'sealed', wl, 'test.jsonl'), rows, 0o600)
                summary['sha256_test_jsonl'] = digest
                summary['sha256_salt_sorted_test_sources'] = test_sources_digest(salt, split[part])
                test_sources[wl] = {'sources': sorted(per_source, key=lambda s: s['source']),
                                    'sha256_test_jsonl': digest}
            else:
                digest = write_jsonl(os.path.join(out, 'release', wl, part + '.jsonl'), rows, 0o644)
                summary['sha256_jsonl'] = digest
                summary['source_list'] = sorted(per_source, key=lambda s: s['source'])
            entry['splits'][part] = summary
            print('%s %-10s sources=%3d records=%5d bytes=%8d mean=%7.2f median=%s sha256=%s' % (
                wl, part, summary['sources'], summary['records'], summary['total_bytes'],
                summary['record_length']['mean'], summary['record_length']['median'], digest[:16]))
        manifest['workloads'][wl] = entry
    write_json(os.path.join(out, 'sealed', 'test-sources.json'), test_sources, mode=0o600)
    os.chmod(os.path.join(out, 'sealed'), 0o700)
    if args.public_out:
        write_json(os.path.join(args.public_out, 'manifest.json'), manifest)
        print('manifest written')


def read_jsonl(path):
    with open(path, 'rb') as fh:
        return [json.loads(line) for line in fh if line.strip()]


def cmd_verify(args):
    salt = load_salt(args.custody)
    full = read_json(sealed(args.custody, 'sources-full.json'))
    manifest = read_json(os.path.join(args.public, 'manifest.json'))
    tests = read_json(sealed(args.custody, 'test-sources.json'))
    problems = []

    def check(ok, text):
        print(('PASS  ' if ok else 'FAIL  ') + text)
        if not ok:
            problems.append(text)

    org_split, release_recs, sealed_recs, test_names = {}, set(), set(), set()
    for wl in ORDER:
        cfg = WORKLOADS[wl]
        org_of = {s['source']: s['org'] for s in full['workloads'][wl]['sources']}
        files = {'train': os.path.join(args.custody, 'release', wl, 'train.jsonl'),
                 'validation': os.path.join(args.custody, 'release', wl, 'validation.jsonl'),
                 'test': sealed(args.custody, wl, 'test.jsonl')}
        where, recs_all, per_source = {}, [], {}
        for part, path in files.items():
            rows = read_jsonl(path)
            key = 'sha256_test_jsonl' if part == 'test' else 'sha256_jsonl'
            summary = manifest['workloads'][wl]['splits'][part]
            check(sha256_hex(open(path, 'rb').read()) == summary[key], '%s %s file hash matches the manifest' % (wl, part))
            check(len(rows) == summary['records'], '%s %s record count matches the manifest' % (wl, part))
            for row in rows:
                rec = base64.b64decode(row['record_b64'])
                where.setdefault(row['source'], set()).add(part)
                per_source[row['source']] = per_source.get(row['source'], 0) + 1
                recs_all.append(rec)
                (sealed_recs if part == 'test' else release_recs).add(rec)
                org_split.setdefault(org_of[row['source']], set()).add((wl, part))
        check(all(len(v) == 1 for v in where.values()), '%s no source appears in two splits' % wl)
        check(len(recs_all) == len(set(recs_all)), '%s no duplicate records' % wl)
        check(all(valid_record(r, cfg) for r in recs_all), '%s every record passes the length and encoding rules' % wl)
        check(max(per_source.values()) <= CAP_PER_SOURCE, '%s no source exceeds the cap of %d' % (wl, CAP_PER_SOURCE))
        names = sorted(n for n, parts in where.items() if parts == {'test'})
        test_names.update(names)
        check(names == sorted(s['source'] for s in tests[wl]['sources']), '%s sealed test source list matches the test file' % wl)
        check(test_sources_digest(salt, names) == manifest['workloads'][wl]['splits']['test']['sha256_salt_sorted_test_sources'],
              '%s test source digest matches the manifest' % wl)
        check(split_sources(list(org_of), salt)['test'] and sorted(split_sources(list(org_of), salt)['test']) == names,
              '%s test split equals the salted ranking' % wl)
        check('source_list' not in manifest['workloads'][wl]['splits']['test'], '%s manifest lists no test sources' % wl)
    check(all(len({part for _, part in v}) == 1 for v in org_split.values()), 'no organisation spans two splits (all workloads)')
    check(all(len(v) == 1 for v in org_split.values()), 'no organisation is used by two workloads')
    check(not (release_recs & sealed_recs), 'no record is in both release and sealed files')

    public_blob = b''
    for root, _, names in os.walk(args.public):
        for name in sorted(names):
            public_blob += open(os.path.join(root, name), 'rb').read() + b'\n'
    low = public_blob.lower()
    leaked = [n for n in test_names if n.lower().encode() in low]
    check(not leaked, 'public files name no test source (%d names checked)' % len(test_names))
    # A bare repository name can also be an ordinary word or part of a released source's
    # name or path. Those hits are listed in the custody copy for a human to judge.
    bare = sorted({n.split('/')[-1].lower() for n in test_names})
    bare_hits = [b for b in bare
                 if re.search(rb'(?<![a-z0-9])' + re.escape(b.encode()) + rb'(?![a-z0-9])', low)]
    write_json(sealed(args.custody, 'verify-bare-name-hits.json'), bare_hits, mode=0o600)
    print('NOTE  %d bare test repository names also occur in the public files as other words; '
          'listed in the custody copy' % len(bare_hits))
    hits = sum(1 for r in (release_recs | sealed_recs) if r in public_blob)
    b64_hits = sum(1 for r in (release_recs | sealed_recs) if base64.b64encode(r) in public_blob)
    check(hits == 0 and b64_hits == 0, 'public files contain no record content (%d records checked)' % len(release_recs | sealed_recs))
    check(salt.hex().encode() not in low, 'public files do not contain the salt')
    builder = sha256_hex(open(os.path.join(args.public, 'build_corpus.py'), 'rb').read())
    check(builder == manifest['builder']['sha256'], 'manifest names this version of the builder')
    mode = os.stat(sealed(args.custody)).st_mode & 0o777
    check(mode == 0o700, 'sealed directory mode is 700')
    print('verify: %s' % ('all checks passed' if not problems else '%d checks failed' % len(problems)))
    sys.exit(1 if problems else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)

    def common(p, work=True):
        p.add_argument('--custody', required=True, help='the custody directory (outside the repository)')
        if work:
            p.add_argument('--work', required=True, help='scratch directory for transient clones and caches')

    p = sub.add_parser('pin'); common(p)
    p.add_argument('--workload', choices=ORDER)
    p.add_argument('--only', nargs='*', help='pin only these sources again')
    p.add_argument('--force', action='store_true')
    p.add_argument('--jobs', type=int, default=4)
    p.set_defaults(fn=cmd_pin)
    p = sub.add_parser('finalize'); common(p)
    p.add_argument('--recheck', help='extract-results.json of a rebuild run; failed sources are dropped')
    p.set_defaults(fn=cmd_finalize)
    p = sub.add_parser('init-salt'); common(p, work=False); p.set_defaults(fn=cmd_init_salt)
    p = sub.add_parser('extract'); common(p)
    p.add_argument('--workload', choices=ORDER)
    p.add_argument('--jobs', type=int, default=4)
    p.set_defaults(fn=cmd_extract)
    p = sub.add_parser('build'); common(p)
    p.add_argument('--out-custody', help='write record files here instead of the custody directory')
    p.add_argument('--public-out', help='directory that receives manifest.json')
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser('verify'); common(p, work=False)
    p.add_argument('--public', required=True, help='the public directory holding manifest.json')
    p.set_defaults(fn=cmd_verify)
    args = ap.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
