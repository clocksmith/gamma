"""Explicit, checksum-bound workspace provisioning; no automatic model execution.

Stages are separate. Download reads only the two approved manifests and official
artifact URLs. Installation is native CPython3.13 CPU-only and offline, into the
private target venv. Neither stage loads candidates, cases or an encoder.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen
import venv
import zipfile

CAP = 4 * 1024 ** 3
RESERVE = 16 * 1024 ** 2
PIP_TOOL = Path('/opt/codex/runtimes/codex-primary-runtime/dependencies/python/lib/python3.12/site-packages/pip')


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 ** 2), b''):
            value.update(chunk)
    return value.hexdigest()


def pinned(path, expected):
    if sha(path) != expected:
        raise ValueError('approved manifest changed')
    return json.loads(Path(path).read_bytes())


def usage(root):
    """Inspect only the dedicated provisioning root, never other user files."""
    total = 0
    for base, directories, files in os.walk(root, followlinks=False):
        for name in files:
            path = Path(base) / name
            if path.is_symlink():
                continue  # venv interpreter links consume no copied target bytes
            info = path.stat()
            total += max(info.st_size, info.st_blocks * 512)
    return total


def budget(root, additional=0):
    used = usage(root)
    free = shutil.disk_usage(root).free
    if additional < 0 or used + additional + RESERVE > CAP or free < additional + RESERVE:
        raise RuntimeError(f'disk budget blocked: used={used} additional={additional} free={free} cap={CAP}')
    return {'workspace_bytes': used, 'free_bytes': free, 'ceiling_bytes': CAP}


def event(root, stage, **fields):
    record = {'time_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'stage': stage, **fields}
    with (root / 'lifecycle.jsonl').open('a') as handle:
        handle.write(json.dumps(record, sort_keys=True) + '\n')
    print(json.dumps(record, sort_keys=True), flush=True)


def artifacts(encoder, cpu):
    result = []
    for row in encoder['files']:
        result.append(dict(name=row['path'], folder='model', bytes=row['bytes'], sha256=row['sha256'], url=row['download_url']))
    torch = cpu['torch']
    result.append(dict(name=unquote(urlparse(torch['wheel_url']).path.rsplit('/', 1)[1]), folder='wheels', bytes=int(torch['wheel_bytes']), sha256=torch['sha256'], url=torch['wheel_url'], package='torch', version=torch['version']))
    for name, row in cpu['packages'].items():
        result.append(dict(name=row['filename'], folder='wheels', bytes=row['bytes'], sha256=row['sha256'], url=row['url'], package=name, version=row['version']))
    if sum(row['bytes'] for row in result) != cpu['combined_download_bytes']:
        raise ValueError('approved artifact denominator mismatch')
    for row in result:
        if Path(row['name']).name != row['name'] or row['name'] in ('', '.', '..'):
            raise ValueError('artifact path is not a basename')
        url = urlparse(row['url'])
        if url.scheme != 'https' or url.hostname not in ('huggingface.co', 'files.pythonhosted.org', 'download-r2.pytorch.org'):
            raise ValueError('artifact URL is not an approved official origin')
    return result


def download_one(root, row):
    target = root / row['folder'] / row['name']; target.parent.mkdir(exist_ok=True)
    if target.exists():
        if target.stat().st_size != row['bytes'] or sha(target) != row['sha256']:
            raise ValueError('existing artifact differs; preserve and inspect: ' + str(target))
        event(root, 'artifact_already_verified', file=row['name']); return
    part = target.with_name(target.name + '.part')
    offset = part.stat().st_size if part.exists() else 0
    if offset > row['bytes']:
        raise ValueError('partial artifact exceeds expected bytes')
    budget(root, row['bytes'] - offset)
    event(root, 'download_started', file=row['name'], expected_bytes=row['bytes'], resume_bytes=offset)
    if offset < row['bytes']:
        headers = {'Range': 'bytes=' + str(offset) + '-'} if offset else {}
        with urlopen(Request(row['url'], headers=headers), timeout=60) as response:
            if offset and (response.status != 206 or not response.headers.get('Content-Range', '').startswith('bytes ' + str(offset) + '-')):
                raise ValueError('server did not honor bounded resume; partial preserved')
            final = urlparse(response.url)
            if final.scheme != 'https': raise ValueError('non-HTTPS artifact redirect')
            total = offset; last = offset
            with part.open('ab' if offset else 'wb') as handle:
                while True:
                    chunk = response.read(min(1024 ** 2, row['bytes'] - total + 1))
                    if not chunk: break
                    if total + len(chunk) > row['bytes']:
                        raise ValueError('server artifact exceeds approved size')
                    budget(root, len(chunk))
                    handle.write(chunk); total += len(chunk)
                    if total - last >= 64 * 1024 ** 2:
                        handle.flush(); event(root, 'download_progress', file=row['name'], bytes=total, expected_bytes=row['bytes']); last = total
    if part.stat().st_size != row['bytes'] or sha(part) != row['sha256']:
        raise ValueError('download checksum/size mismatch; partial preserved: ' + str(part))
    part.rename(target)
    event(root, 'artifact_verified', file=row['name'], bytes=row['bytes'], sha256=row['sha256'], **budget(root))


def inspect_wheels(root, rows):
    unpacked = 0; notices = []; count = 0
    for row in rows:
        path = root / row['folder'] / row['name']
        if path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            raise ValueError('artifact changed before install')
        if row['folder'] != 'wheels': continue
        with zipfile.ZipFile(path) as wheel:
            for entry in wheel.infolist():
                if entry.filename.startswith('/') or '..' in Path(entry.filename).parts:
                    raise ValueError('wheel contains unsafe path')
                unpacked += entry.file_size
                if 'license' in entry.filename.lower() or 'notice' in entry.filename.lower():
                    notices.append({'wheel': row['name'], 'member': entry.filename, 'bytes': entry.file_size})
        count += 1
    receipt = {'wheel_count': count, 'zip_uncompressed_bytes': unpacked, 'license_notice_members': notices,
               'note': 'ZIP metadata counts, not execution; installed footprint includes additional filesystem metadata'}
    (root / 'wheel-inspection.json').write_text(json.dumps(receipt, sort_keys=True, indent=2) + '\n')
    budget(root, 2 * unpacked + 128 * 1024 ** 2)
    event(root, 'wheel_inspection_complete', wheel_count=count, zip_uncompressed_bytes=unpacked, **budget(root))
    return receipt


def native_install(root, rows):
    if sys.version_info[:2] != (3, 13) or platform.machine() != 'x86_64' or sys.executable != '/usr/bin/python3':
        raise RuntimeError('installation requires the approved native /usr/bin/python3 CPython3.13 x86_64')
    inspect_wheels(root, rows)
    target = root / 'venv'
    if not (target / 'pyvenv.cfg').exists():
        budget(root, 128 * 1024 ** 2); venv.EnvBuilder(with_pip=False, symlinks=True).create(target)
    interpreter = target / 'bin' / 'python'
    if not PIP_TOOL.joinpath('__main__.py').is_file():
        raise RuntimeError('existing trusted pip tool unavailable; no unpinned bootstrap download permitted')
    lock = root / 'requirements.lock'
    lock.write_text(''.join(f"{row['package']}=={row['version']} --hash=sha256:{row['sha256']}\n" for row in rows if row['folder'] == 'wheels'))
    env = dict(os.environ, PIP_NO_INDEX='1', PIP_DISABLE_PIP_VERSION_CHECK='1', PIP_NO_CACHE_DIR='1', PYTHONDONTWRITEBYTECODE='1', TMPDIR=str(root / 'tmp'))
    (root / 'tmp').mkdir(exist_ok=True)
    command = [sys.executable, str(PIP_TOOL), '--python', str(interpreter), 'install', '--no-index', '--no-deps', '--no-cache-dir', '--no-compile', '--only-binary=:all:', '--require-hashes', '--find-links', str(root / 'wheels'), '-r', str(lock)]
    version = subprocess.check_output([sys.executable, str(PIP_TOOL), '--version'], text=True, env=env, timeout=20).strip()
    event(root, 'native_install_started', installer=version, installer_main_sha256=sha(PIP_TOOL / '__main__.py'))
    with (root / 'install.log').open('a') as log:
        process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env)
        try:
            while process.poll() is None:
                budget(root); time.sleep(.25)
        except BaseException:
            process.terminate(); process.wait(timeout=10); raise
    if process.returncode:
        raise RuntimeError('offline installation failed; inspect install.log')
    event(root, 'native_install_complete', **budget(root))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('encoder', 'cpu', 'root'): p.add_argument('--' + name, type=Path, required=True)
    for name in ('encoder-sha256', 'cpu-sha256'): p.add_argument('--' + name, required=True)
    p.add_argument('--stage', choices=('download', 'inspect', 'install'), required=True)
    args = p.parse_args(argv)
    root = args.root.absolute()
    if not str(root).startswith('/workspace/shared/') or root.is_symlink():
        raise ValueError('dedicated nonsymlink workspace/shared root required')
    root.mkdir(exist_ok=True)
    encoder = pinned(args.encoder, args.encoder_sha256); cpu = pinned(args.cpu, args.cpu_sha256)
    rows = artifacts(encoder, cpu)
    event(root, 'stage_started', requested_stage=args.stage, approved_download_bytes=cpu['combined_download_bytes'], **budget(root))
    try:
        if args.stage == 'download':
            for row in rows: download_one(root, row)
            inspect_wheels(root, rows)
        elif args.stage == 'inspect': inspect_wheels(root, rows)
        else: native_install(root, rows)
        event(root, 'stage_complete', requested_stage=args.stage, **budget(root))
    except BaseException as error:
        event(root, 'stage_blocked', requested_stage=args.stage, error=type(error).__name__, detail=str(error))
        raise


if __name__ == '__main__': main()
