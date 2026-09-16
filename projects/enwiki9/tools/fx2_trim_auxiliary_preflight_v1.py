#!/usr/bin/env python3
"""Materialize and test the separate PPM auxiliary packaging realization.

No native codec, model, dictionary compression, or enwik9 prediction executes.
The only compiled code is the extracted option-policy/header synthetic probe.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lib.fx2_trim_auxiliary_ppm_v1 import materialize, PREIMAGES, HELPERS
from tools.fx2_expert_release250k_v3 import source_zip

ID = 'fx2_trim_auxiliary_preflight_v1'
PARENT = 'results/fx2_expert_release250k_v3/P-source.zip'
PARENT_SHA = 'c44d941f95bd8504d63ed6ea5112af3ce15aeffb6874ebddb66596ce083c3cf6'
SOURCES = [
    'lib/fx2_trim_auxiliary_ppm_v1.py',
    'lib/fx2_trim_auxiliary_pack_v1.py',
    'tests/test_fx2_trim_auxiliary_ppm_v1.py',
    'tools/fx2_trim_auxiliary_preflight_v1.py',
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def record(path):
    data = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
                bytes=len(data), sha256=sha(data))


def main():
    out = ROOT / 'results' / ID
    out.mkdir(exist_ok=False)
    inputs = [record(ROOT / p) for p in SOURCES + [PARENT]]
    if inputs[-1]['sha256'] != PARENT_SHA:
        raise ValueError('parent source ZIP differs')
    with zipfile.ZipFile(ROOT / PARENT) as z:
        parent = {n: z.read(n) for n in z.namelist()}
    child = materialize(parent, (ROOT / SOURCES[1]).read_bytes())
    for name, members in [('P-source.zip', parent), ('D-source.zip', child),
                          ('D-repeat-source.zip', materialize(parent, (ROOT / SOURCES[1]).read_bytes()))]:
        source_zip(out / name, members)
    if (out / 'P-source.zip').read_bytes() != (ROOT / PARENT).read_bytes():
        raise ValueError('unchanged parent ZIP serialization differs')
    if (out / 'D-source.zip').read_bytes() != (out / 'D-repeat-source.zip').read_bytes():
        raise ValueError('independent materialization differs')
    command = [sys.executable, '-m', 'unittest', 'tests.test_fx2_trim_auxiliary_ppm_v1', '-v']
    with (out / 'unit.log').open('w') as log:
        result = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    receipt = dict(
        schema='gamma.enwiki9.synthetic-packaging-preflight.v1', id=ID,
        candidate_id='fx2_trim_auxiliary_ppm_v1',
        scope='Source materialization and extracted option-policy/header probes only.',
        inputs=inputs, source_preimages=PREIMAGES,
        changed_existing_members=[n for n in parent if parent[n] != child[n]],
        added_members=sorted(set(child) - set(parent)),
        helper_commands=[c + ' --ppmd-only' for c in HELPERS],
        packages={a: record(out / (a + '-source.zip')) for a in 'PD'},
        source_zip_increment_bytes=(out / 'D-source.zip').stat().st_size - (out / 'P-source.zip').stat().st_size,
        materialization_repeat_byte_equal=True, unchanged_parent_zip_byte_equal=True,
        tests=dict(command=command, returncode=result.returncode, log=record(out / 'unit.log'),
                   compiler=record(Path('/usr/bin/g++').resolve()),
                   python=record(Path(sys.executable).resolve()),
                   native_codec_executed=False, test_count=6,
                   policy_probe_readable_file_check='stubbed; no file-availability claim'),
        complete_submission_package=False, full_corpus_score_bytes=None,
        objective_credit=0, auxiliary_compressed_sizes=None, native_binary_delta_bytes=None,
        remaining=['Fresh native clean builds and deterministic rebuilds.',
                   'Both exact auxiliary inverses and repeated compressed asset identities.',
                   'Actual self-extractor child invocations with no external assets.',
                   'Fresh main native archive/reconstruction parity for this new binary.',
                   'Complete counted package, option, license and platform closure.'],
        all_preflight_checks_pass=result.returncode == 0)
    (out / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
