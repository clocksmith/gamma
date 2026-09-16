#!/usr/bin/env python3
"""Audit the frozen trimmed ELF's load-time closure without entering the codec.

No corpus, model, compiler, full /usr mount, installation or network is used.
This is a diagnostic receipt, not runtime, license or submission qualification.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BINARY = ROOT / 'results/fx2_expert_release250k_v3/work/native/cmix-P'
EXPECTED_SHA256 = '1bbae21a0a5a8e50669bce1e68f565296155af4b7610c2a7ac079b8d8f4aa890'
LOADER = Path('/lib64/ld-linux-x86-64.so.2')
READELF = Path('/usr/bin/readelf')
BWRAP = Path('/usr/bin/bwrap')
REQUIRED = {'libstdc++.so.6', 'libm.so.6', 'libgcc_s.so.1', 'libc.so.6'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(path):
    p = Path(path)
    real = p.resolve(strict=True)
    return {'path': str(p), 'resolved_path': str(real),
            'bytes': real.stat().st_size,
            'sha256': hashlib.sha256(real.read_bytes()).hexdigest()}


def write(path, obj):
    with path.open('x') as f:
        json.dump(obj, f, indent=2, sort_keys=True)
        f.write('\n')


def probe(out, label, command):
    # A bounded loader/readelf inspection; subprocess never receives codec args.
    cmd = [str(v) for v in command]
    completed = subprocess.run(cmd, env={'LC_ALL': 'C', 'PATH': '/usr/bin:/bin'},
                               cwd=ROOT, text=True, capture_output=True, timeout=15)
    row = {'command': cmd, 'returncode': completed.returncode,
           'stdout': completed.stdout, 'stderr': completed.stderr}
    write(out / (label + '.json'), row)
    return row


def listed_paths(text):
    rows = re.findall(r'^\s*(\S+) => (\/\S+) \(0x[0-9a-f]+\)$', text, re.M)
    require(len(rows) == len(dict(rows)), 'duplicate loader listing name')
    return dict(rows)


def dynamic(out, label, path):
    row = probe(out, label, [READELF, '--dynamic', '--wide', path])
    require(row['returncode'] == 0, 'readelf failed')
    needed = re.findall(r'\(NEEDED\).*?\[(.*?)\]', row['stdout'])
    sonames = re.findall(r'\(SONAME\).*?\[(.*?)\]', row['stdout'])
    require(len(sonames) <= 1, 'multiple SONAMEs')
    return {'needed': needed, 'soname': sonames[0] if sonames else None}


def sandbox_command(providers, omitted=None):
    cmd = [BWRAP, '--unshare-all', '--die-with-parent', '--new-session',
           '--clearenv', '--dir', '/runtime', '--dir', '/runtime/lib',
           '--dir', '/package', '--ro-bind', BINARY, '/package/cmix',
           '--setenv', 'LC_ALL', 'C', '--chdir', '/package']
    for name, provider in sorted(providers.items()):
        if name != omitted:
            cmd += ['--ro-bind', provider['resolved_path'], '/runtime/lib/' + name]
    return cmd + ['--', '/runtime/lib/ld-linux-x86-64.so.2', '--inhibit-cache',
                  '--library-path', '/runtime/lib', '--list', '/package/cmix']


def audit(out):
    require(identity(BINARY)['sha256'] == EXPECTED_SHA256, 'frozen binary differs')
    bound = {str(p): identity(p) for p in (BINARY, LOADER, READELF, BWRAP)}
    host = probe(out, 'host-loader-list', [LOADER, '--list', BINARY])
    require(host['returncode'] == 0, 'host listing failed')
    paths = listed_paths(host['stdout'])
    require(set(paths) == REQUIRED, 'unexpected host dependencies')
    providers = {name: identity(path) for name, path in paths.items()}
    providers['ld-linux-x86-64.so.2'] = identity(LOADER)
    binary_dynamic = dynamic(out, 'binary-dynamic', BINARY)
    require(set(binary_dynamic['needed']) == REQUIRED, 'direct dependency set changed')
    graph = {'cmix': binary_dynamic}
    for name, provider in sorted(providers.items()):
        graph[name] = dynamic(out, 'dynamic-' + name, provider['resolved_path'])
        require(graph[name]['soname'] == name, 'SONAME differs from requested provider')
        require(set(graph[name]['needed']) <= set(providers), 'unresolved transitive dependency')
    # Check reachability too: every supplied library must be necessary in the graph.
    reached, pending = set(), list(binary_dynamic['needed'])
    while pending:
        name = pending.pop()
        if name not in reached:
            reached.add(name)
            pending.extend(graph[name]['needed'])
    require(reached == set(providers), 'unneeded or unreachable library supplied')
    positive = probe(out, 'restricted-loader-list', sandbox_command(providers))
    require(positive['returncode'] == 0, 'restricted listing failed')
    restricted = listed_paths(positive['stdout'])
    require(set(restricted) == REQUIRED, 'restricted listing dependency set differs')
    require(all(path == '/runtime/lib/' + name for name, path in restricted.items()),
            'resolved outside declared library mounts')
    controls = []
    for name in sorted(REQUIRED):
        row = probe(out, 'missing-' + name, sandbox_command(providers, omitted=name))
        require(row['returncode'] != 0 and name in row['stderr'],
                'missing-library control did not fail as expected')
        controls.append({'omitted': name, 'returncode': row['returncode'],
                         'failed_with_missing_library_name': True})
    for before in list(bound.values()) + list(providers.values()):
        require(identity(before['path']) == before, 'bound artifact changed during audit')
    # Licensing provenance is inventoried; package metadata is not legal approval.
    packages = {}
    for name, provider in sorted(providers.items()):
        row = probe(out, 'owner-' + name,
                    ['/usr/bin/dpkg-query', '-S', provider['resolved_path']])
        require(row['returncode'] == 0, 'no local package owner for runtime library')
        packages[name] = row['stdout'].strip()
    return {
        'schema': 'gamma.enwiki9.trim-load-closure.v1',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'status': 'restricted-load-time-closure-pass',
        'binary': identity(BINARY), 'tools': bound, 'providers': providers,
        'dynamic_dependency_graph': graph, 'local_package_ownership': packages,
        'missing_library_controls': controls,
        'supplied_runtime_file_bytes': sum(x['bytes'] for x in providers.values()),
        'reconstruction_credit_bytes': 0, 'compression_credit_bytes': 0,
        'full_corpus_score_bytes': None, 'complete_submission_package': False,
        'codec_main_executed': False, 'corpus_or_model_read': False,
        'native_source_or_binary_changed': False,
        'network_available_in_restricted_probe': False,
        'full_usr_mounted': False,
        'scope': 'Transitive ELF load-time providers on this host only. Loader --list never enters codec main.',
        'unresolved': [
            'Application execution may open additional files or load libraries dynamically.',
            'Model, dictionary, filesystem, scratch and codec encode/decode closure remain separate.',
            'Copied-header lineage, model permission and libdevice transcription permission remain unresolved.',
            'Compiler/source equivalence, cross-CPU parity and target-system library availability remain unproved.',
            'Library bytes here are an inventory, not a chosen official counted packaging form.',
            'Exact full1G artifact, complete package accounting and calibrated resource eligibility are absent.'
        ]
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True,
                        help='new exclusive directory beneath operations/provenance')
    args = parser.parse_args()
    out = args.out.resolve()
    require(out.is_relative_to(ROOT / 'operations/provenance'), 'output outside provenance')
    out.mkdir(parents=False, exist_ok=False)
    try:
        result = audit(out)
    except Exception as exc:
        write(out / 'failure.json', {'error': repr(exc), 'codec_main_executed': False})
        raise
    result['audit_source'] = identity(__file__)
    write(out / 'receipt.json', result)
    print(json.dumps({'status': result['status'], 'receipt': str(out / 'receipt.json'),
                      'runtime_bytes': result['supplied_runtime_file_bytes']}))


if __name__ == '__main__':
    main()
