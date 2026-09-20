"""Independent synthetic checks of the unchanged user import, not corpus evidence."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

IMPORT = Path(__file__).resolve().parents[1] / 'external/crg-import-20260920'
CASES = {
    'empty': b'',
    'binary': bytes(range(256)) * 2,
    'xml': (b'<page><title>Alpha Delta Gamma Theta</title><text xml:space="preserve">'
            b'Alpha Theta [[Delta]] &amp; Theta.</text></page>') * 4,
    'malformed': b'<text a="quoted > marker">abc\x00\xff [[abc|x] </title>\n' * 3,
}


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope='module')
def codecs(tmp_path_factory):
    work = tmp_path_factory.mktemp('crg-import-build')
    binaries = {}
    for name, path in (('optimized', IMPORT / 'optimized/crg_core.cpp'),
                       ('block', IMPORT / 'block/src/crg.cpp')):
        target = work / name
        subprocess.run(['g++', '-std=c++17', '-O1', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=undefined', '-fno-sanitize-recover=all',
                        str(path), '-o', str(target)], check=True, timeout=60)
        binaries[name] = target
    ref = load('crg_reference', IMPORT / 'optimized/crg_reference.py')
    previous = sys.modules.get('crg_reference')
    sys.modules['crg_reference'] = ref
    try:
        fast = load('import_crg_fast', IMPORT / 'optimized/crg_fast.py')
    finally:
        if previous is None:
            sys.modules.pop('crg_reference', None)
        else:
            sys.modules['crg_reference'] = previous
    block = load('import_crg_block', IMPORT / 'block/compress.py')
    return ref, fast, block, binaries


@pytest.mark.parametrize('case', CASES)
@pytest.mark.parametrize('profile', (0, 1))
@pytest.mark.parametrize('arm', ('parent', 'bookkeeping', 'independent', 'shared', 'wrong'))
def test_optimized_cross_language_archive_and_inverse(codecs, tmp_path, case, profile, arm):
    ref, fast, _, binaries = codecs
    raw = tmp_path / 'input'
    raw.write_bytes(CASES[case])
    py_archive, native_archive = tmp_path / 'python.crg', tmp_path / 'native.crg'
    ref.compress(raw, py_archive, arm=arm, profile=profile, witness=True, time_limit=20)
    fast.encode(raw, native_archive, arm=arm, profile=profile,
                binary=binaries['optimized'], timeout=20)
    assert py_archive.read_bytes() == native_archive.read_bytes()
    # Decoder calls receive only their archive, never the original bytes.
    py_inverse, native_inverse = tmp_path / 'py.inverse', tmp_path / 'native.inverse'
    raw.unlink()
    ref.decompress(native_archive, py_inverse, witness=True, time_limit=20)
    fast.decode(py_archive, native_inverse, binary=binaries['optimized'], timeout=20)
    assert py_inverse.read_bytes() == native_inverse.read_bytes() == CASES[case]
    repeat = tmp_path / 'repeat.crg'
    fast.encode(native_inverse, repeat, arm=arm, profile=profile,
                binary=binaries['optimized'], timeout=20)
    assert repeat.read_bytes() == native_archive.read_bytes()


@pytest.mark.parametrize('case', CASES)
@pytest.mark.parametrize('method', ('stored', 'deflate', 'bzip2', 'lzma', 'context', 'role-history', 'auto'))
def test_block_container_inverse_repeat_and_boundaries(codecs, tmp_path, case, method):
    _, _, block, binaries = codecs
    raw, archive = tmp_path / 'input', tmp_path / 'archive'
    raw.write_bytes(CASES[case])
    report = block.compress_file(raw, archive, block_size=257, method=method, cpp=binaries['block'])
    raw.unlink()
    restored = tmp_path / 'restored'
    block.decompress_file(archive, restored, cpp=binaries['block'], max_output=len(CASES[case]))
    assert restored.read_bytes() == CASES[case]
    repeat = tmp_path / 'repeat'
    block.compress_file(restored, repeat, block_size=257, method=method, cpp=binaries['block'])
    assert repeat.read_bytes() == archive.read_bytes()
    if method == 'auto':
        for row in report['blocks']:
            assert row['payload_bytes'] == min(row['candidate_payloads'].values())


@pytest.mark.parametrize('bundle', ('optimized', 'block'))
@pytest.mark.parametrize('fault', ('payload-bit', 'truncated', 'trailing', 'output-cap'))
def test_corruption_or_output_limit_never_publishes(codecs, tmp_path, bundle, fault):
    _, fast, block, binaries = codecs
    raw, archive, restored = tmp_path / 'input', tmp_path / 'archive', tmp_path / 'restored'
    raw.write_bytes(CASES['xml'])
    if bundle == 'optimized':
        fast.encode(raw, archive, arm='shared', binary=binaries['optimized'], timeout=20)
    else:
        block.compress_file(raw, archive, method='role-history', cpp=binaries['block'])
    data = archive.read_bytes()
    if fault == 'payload-bit':
        data = data[:-1] + bytes([data[-1] ^ 128])
    elif fault == 'truncated':
        data = data[:-1]
    elif fault == 'trailing':
        data += b'\0'
    archive.write_bytes(data)
    cap = len(CASES['xml']) - (fault == 'output-cap')
    with pytest.raises((ValueError, subprocess.SubprocessError)):
        if bundle == 'optimized':
            fast.decode(archive, restored, binary=binaries['optimized'], max_output=cap, timeout=20)
        else:
            block.decompress_file(archive, restored, cpp=binaries['block'], max_output=cap)
    assert not restored.exists()
