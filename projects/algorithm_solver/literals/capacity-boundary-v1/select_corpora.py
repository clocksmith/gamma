#!/usr/bin/env python3
"""Choose the benchmark corpora by a fixed, seeded rule and write instances.json. Reads Git objects only; solves nothing.

    python3 -B select_corpora.py --gamma PATH --fawn PATH --doppler PATH --reploid PATH

Each PATH is a full clone that contains the pinned commit. Nothing is checked out; files are read with `git cat-file`.

The rule:
- A candidate file is tracked at the pin, has one of the group's extensions, is 300 to 2,500 bytes, and is UTF-8.
- A candidate corpus is the first four candidate files of one group in one directory, in sorted name order,
  together at most 6,000 bytes, pairwise distinct, using 60 to 70 distinct characters.
- Directories used by the earlier independent evaluation are excluded, and so is Gamma's projects/algorithm_solver.
- Candidates are ordered by SHA-256 of "SEED|repository|directory|group". The first four of each group are taken,
  with at most two from one repository per group.
- A candidate that shares a file's content with a corpus already taken is skipped. This condition was added after
  the first run of the rule chose two corpora that duplicated others, and before any method was run on any corpus.
"""
import argparse
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 'capacity-boundary-v1/2026-11-22'
PINS = {
    'gamma': '59ff04415ff2afd04ff2ed451340f4f02852bf18',
    'fawn': 'a281360ff04321f08e5627c5309503d0259a0e70',
    'doppler': 'bfee8cd4376b0e3da4005cb4b85d53df907faa53',
    'reploid': '3ced04b91913e6aee2a4bb5a8778291019058663',
}
GROUPS = {'js': ('.js', '.mjs', '.ts'), 'py': ('.py',), 'c': ('.h', '.c', '.cc', '.cpp')}
SKIP_PARTS = {'node_modules', 'vendor', 'third_party', 'dist', 'build'}
SKIP_PREFIX = {'gamma': ('projects/algorithm_solver/',)}
FILE_BYTES, CORPUS_BYTES, ALPHABET, PER_GROUP, PER_REPOSITORY = (300, 2500), 6000, (60, 70), 4, 2
EARLIER = os.path.join(HERE, '..', 'capacity-diagnostic-v1', 'independent-eval', 'independent-instances.json')


def git(repo, *args):
    return subprocess.check_output(['git', '-C', repo, *args])


class Blobs:
    """Read file contents at a pin through one `git cat-file --batch` process."""

    def __init__(self, repo):
        self.process = subprocess.Popen(['git', '-C', repo, 'cat-file', '--batch'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def read(self, pin, path):
        self.process.stdin.write(f'{pin}:{path}\n'.encode())
        self.process.stdin.flush()
        header = self.process.stdout.readline().split()
        if header[-1] == b'missing':
            raise KeyError(path)
        raw = self.process.stdout.read(int(header[2]))
        self.process.stdout.read(1)
        return raw


def candidates(name, repo):
    """{(directory, group): sorted file names} for files that pass the size and path rules."""
    out = {}
    for line in git(repo, 'ls-tree', '-r', '-l', PINS[name]).decode('utf-8', 'replace').splitlines():
        meta, path = line.split('\t', 1)
        kind, size = meta.split()[1], meta.split()[3]
        if kind != 'blob' or not FILE_BYTES[0] <= int(size) <= FILE_BYTES[1]:
            continue
        parts = path.split('/')
        if SKIP_PARTS & set(parts) or any(path.startswith(p) for p in SKIP_PREFIX.get(name, ())):
            continue
        for group, extensions in GROUPS.items():
            if path.endswith(extensions):
                out.setdefault(('/'.join(parts[:-1]), group), []).append(parts[-1])
    return {key: sorted(names) for key, names in out.items()}


def main():
    parser = argparse.ArgumentParser()
    for name in PINS:
        parser.add_argument('--' + name, required=True)
    repos = vars(parser.parse_args())
    earlier = json.load(open(EARLIER))['corpora']
    used = {(c['repo'], os.path.dirname(f['path'])) for c in earlier.values() for f in c['files']}

    ranked = []
    for name, repo in repos.items():
        for (directory, group), names in candidates(name, repo).items():
            if (name, directory) not in used:
                digest = hashlib.sha256(f'{SEED}|{name}|{directory}|{group}'.encode()).hexdigest()
                ranked.append((digest, name, directory, group, names))
    ranked.sort()

    blobs = {name: Blobs(repo) for name, repo in repos.items()}
    chosen, taken, considered, seen_files = [], {}, 0, set()
    for digest, name, directory, group, names in ranked:
        if sum(1 for c in chosen if c['group'] == group) >= PER_GROUP or taken.get((name, group), 0) >= PER_REPOSITORY:
            continue
        files, texts = [], []
        for file_name in names:
            raw = blobs[name].read(PINS[name], f"{directory + '/' if directory else ''}{file_name}")
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                continue
            files.append({'path': f"{directory + '/' if directory else ''}{file_name}", 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
            texts.append(text)
            if len(texts) == 4:
                break
        considered += 1
        alphabet = len(set(''.join(texts)))
        if len(texts) < 4 or len(set(texts)) < 4 or sum(f['bytes'] for f in files) > CORPUS_BYTES or not ALPHABET[0] <= alphabet <= ALPHABET[1]:
            continue
        if any(f['sha256'] in seen_files for f in files):          # no file content appears in two corpora
            continue
        seen_files.update(f['sha256'] for f in files)
        taken[(name, group)] = taken.get((name, group), 0) + 1
        chosen.append({'group': group, 'repo': name, 'pin': PINS[name], 'directory': directory, 'order': digest[:16],
                       'files': files, 'bytes': sum(f['bytes'] for f in files), 'alphabet': alphabet, 'programs': texts})
        if len(chosen) == PER_GROUP * len(GROUPS):
            break

    chosen.sort(key=lambda c: (list(GROUPS).index(c['group']), c['order']))
    corpora = {}
    for c in chosen:
        number = sum(1 for k in corpora if k.startswith(c['group'].upper())) + 1
        corpora[f"{c['group'].upper()}-{number}"] = c
    out = {'schema': 'capacity-boundary-instances/v1', 'seed': SEED, 'pins': PINS, 'candidateDirectoriesRanked': len(ranked),
           'candidateCorporaRead': considered, 'corpora': corpora}
    with open(os.path.join(HERE, 'instances.json'), 'w') as f:
        json.dump(out, f, indent=1)
        f.write('\n')
    print(f'{len(ranked)} candidate directories, {considered} read, {len(corpora)} chosen')
    for key, c in corpora.items():
        print(f"  {key:5} {c['repo']:8} alphabet {c['alphabet']} bytes {c['bytes']:5} {c['directory']}")


if __name__ == '__main__':
    main()
