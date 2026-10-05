#!/usr/bin/env python3
"""Extract hash-pinned campaign dependencies without changing host packages."""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'operations/planning/lexth11c_local_dependencies_20261005.json'
BASE = ROOT / 'external/lexth11c-campaign'

def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def fetch(row):
    dest = BASE / 'deps' / row['filename']
    if not dest.exists():
        partial = dest.with_suffix(dest.suffix + '.partial')
        subprocess.run(['curl', '-fLsS', '--retry', '3', '--max-time', '1800',
                        row['url'], '-o', str(partial)], check=True)
        partial.rename(dest)
    if digest(dest) != row['sha256'] or ('bytes' in row and dest.stat().st_size != row['bytes']):
        raise ValueError('dependency identity differs: ' + row['package'])
    print(json.dumps({'verified_dependency': row['package'], 'version': row['version'],
                      'bytes': dest.stat().st_size, 'sha256': row['sha256']}), flush=True)
    return dest

def main():
    plan = json.loads(PLAN.read_bytes())
    started = time.monotonic()
    with concurrent.futures.ThreadPoolExecutor(max_workers=plan['caps']['download_workers']) as pool:
        paths = list(pool.map(fetch, plan['assets']))
    tree = BASE / 'toolchain'
    tree.mkdir(exist_ok=True)
    for row, path in zip(plan['assets'], paths):
        if path.suffix == '.deb':
            subprocess.run(['dpkg-deb', '--extract', str(path), str(tree)], check=True)
        elif row['package'] == 'upx':
            with tarfile.open(path) as t:
                member = t.getmember('upx-5.1.1-amd64_linux/upx')
                target = tree / 'usr/local/bin/upx'
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(t.extractfile(member).read())
                target.chmod(0o755)
            if digest(target) != '6cf3932e8d94a81b705ca7714731dff7a25d4745feee15ef532c20fe52ec8474':
                raise ValueError('UPX executable differs')
        else:
            with tarfile.open(path) as t:
                t.extractall(BASE / 'gpu-python', filter='data')
        if time.monotonic() - started >= plan['caps']['elapsed_stop_seconds']:
            raise TimeoutError('provisioning elapsed stop')
        used = sum(p.stat().st_size for p in BASE.rglob('*') if p.is_file())
        if used > plan['caps']['scratch_bytes']:
            raise ValueError('provisioning scratch stop')
    files = []
    for path in sorted(tree.rglob('*')):
        if path.is_symlink():
            files.append({'path': path.relative_to(BASE).as_posix(), 'symlink': os.readlink(path)})
        elif path.is_file():
            files.append({'path': path.relative_to(BASE).as_posix(), 'bytes': path.stat().st_size,
                          'sha256': digest(path)})
    receipt = {'schema': 'gamma.enwiki9.campaign-local-provisioning.v1',
               'plan_sha256': digest(PLAN), 'assets': plan['assets'], 'files': files,
               'host_packages_changed': False, 'host_root_scripts_run': False,
               'driver_kernel_reboot_changes': False, 'elapsed_seconds': time.monotonic()-started}
    target = ROOT / 'operations/provenance/lexth11c_local_toolchain_20261005.json'
    payload = (json.dumps(receipt, sort_keys=True, separators=(',', ':'))+'\n').encode()
    with target.open('xb') as f:
        f.write(payload)
    target.chmod(0o444)
    print(json.dumps({'provisioned': len(files), 'receipt': str(target)}), flush=True)

if __name__ == '__main__':
    main()
