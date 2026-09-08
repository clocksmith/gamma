"""Retained bounded synthetic execution; no corpus/model access or native claim."""
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parents[1]))
os.sched_setaffinity(0, {3})
resource.setrlimit(resource.RLIMIT_AS, (536870912, 536870912))
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
resource.setrlimit(resource.RLIMIT_FSIZE, (67108864, 67108864))
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'


def write(path, content):
    with path.open('xb') as output:
        output.write(content)


def document(path, value):
    write(path, (json.dumps(value, indent=2, sort_keys=True) + '\n').encode())


def ref(path):
    raw = path.read_bytes()
    return dict(path=str(path.relative_to(ROOT)), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


if sys.argv[1] == 'phase':
    from projects.enwiki9.tests.test_residual_ratio_v1 import FixturePredictor
    from projects.enwiki9.lib import predictor
    arm, action, input_name, output_name = sys.argv[2:]
    data = Path(input_name).read_bytes()
    if len(data) > 8192:
        raise ValueError('input size ceiling')
    model = FixturePredictor(arm)
    before = time.monotonic()
    output = (predictor.decode(data, model, maximum_bytes=4096) if action == 'decode'
              else predictor.encode(data, model))
    elapsed = time.monotonic() - before
    out = Path(output_name)
    write(out, output)
    write(out.with_suffix(out.suffix + '.state'), model.serialize())
    usage = resource.getrusage(resource.RUSAGE_SELF)
    document(out.with_suffix(out.suffix + '.json'), dict(
        arm=arm, action=action, output=ref(out), input=ref(Path(input_name)),
        probability_sha256=model.probabilities.hexdigest(),
        boundary_sha256=model.boundaries.hexdigest(), bit_boundaries=model.position,
        state_sha256=model.state_digest(), state_bytes=len(model.serialize()),
        cpu_affinity=sorted(os.sched_getaffinity(0)), threads=1,
        codec_elapsed_seconds=elapsed, process_user_seconds=usage.ru_utime,
        process_system_seconds=usage.ru_stime, peak_rss_bytes=usage.ru_maxrss * 1024))
else:
    target = ROOT / 'results/fx2_residual_ratio_synthetic_v1' / sys.argv[1]
    target.mkdir(exist_ok=False)
    env = dict(os.environ, PYTHONPATH=str(ROOT.parents[1]))
    start = time.monotonic()
    log = subprocess.run([sys.executable, '-m', 'unittest', 'tests.test_residual_ratio_v1', '-v'],
                         cwd=ROOT, env=env, capture_output=True, timeout=45)
    write(target/'tests.stdout', log.stdout); write(target/'tests.stderr', log.stderr)
    if log.returncode:
        raise RuntimeError('synthetic tests failed; retained outputs')
    rows = []
    for name, raw in [('constant', b'A' * 1024), ('balanced', bytes(range(256)) * 4)]:
        fixture = target / (name + '.raw'); write(fixture, raw)
        arms = {}
        for arm in ('P', 'K', 'D', 'S'):
            phases = []
            for action in ('encode', 'decode', 'repeat'):
                path = target / (name + '-' + arm + '-' + action + '.bin')
                inp = target / (name + '-' + arm + '-encode.bin') if action == 'decode' else fixture
                command = [sys.executable, str(Path(__file__).resolve()), 'phase', arm, action, str(inp), str(path)]
                run = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=15)
                write(path.with_suffix('.stdout'), run.stdout); write(path.with_suffix('.stderr'), run.stderr)
                if run.returncode:
                    raise RuntimeError('phase failed; retained outputs')
                phases.append(json.loads(path.with_suffix(path.suffix + '.json').read_text()))
            paths = [ROOT / p['output']['path'] for p in phases]
            assert paths[0].read_bytes() == paths[2].read_bytes()
            assert paths[1].read_bytes() == raw
            for key in ('probability_sha256', 'boundary_sha256', 'state_sha256', 'bit_boundaries'):
                assert len({p[key] for p in phases}) == 1
            arms[arm] = dict(archive_bytes=paths[0].stat().st_size, phases=phases)
        assert arms['P']['phases'][0]['output']['sha256'] == arms['K']['phases'][0]['output']['sha256']
        assert arms['P']['phases'][0]['probability_sha256'] == arms['K']['phases'][0]['probability_sha256']
        rows.append(dict(fixture=ref(fixture), arms=arms,
                         treatment_archive_saving=arms['P']['archive_bytes']-arms['D']['archive_bytes']))
    files = [p for p in target.rglob('*') if p.is_file()]
    total = sum(p.stat().st_size for p in files)
    assert total < 67108864 and time.monotonic() - start < 180
    sources = [ROOT/p for p in ('lib/residual_ratio_v1.py', 'lib/predictor.py',
                               'tests/test_residual_ratio_v1.py',
                               'results/fx2_residual_ratio_synthetic_v1/reproduce.py')]
    receipt = dict(schema='gamma.enwiki9.residual-ratio-synthetic.v1',
                   objective_bytes=90000000, corpus_bytes=0, objective_credit_bytes=0,
                   source_inventory=[ref(p) for p in sources],
                   plan=ref(ROOT/'operations/provenance/fx2_residual_ratio_synthetic_v1_plan.json'),
                   unit_tests_passed=9, phase_count=24, rows=rows,
                   scratch_bytes_before_receipt=total, artifacts=[ref(p) for p in sorted(files)],
                   complete_package_bytes=None,
                   limitations=['Uniform synthetic parent, not native FX2.',
                                'Probability and predictor-state witnesses include every bit; no new native coder-state instrumentation.',
                                'Python runtime and complete dependency accounting unresolved.'],
                   next_action='Implement a separately identified native adapter; establish half-probability mapping and P/K identity before any scientific corpus gate.')
    document(target/'receipt.json', receipt)
    print(json.dumps(dict(phase_count=24, sizes=[{a:r['arms'][a]['archive_bytes'] for a in ('P','K','D','S')} for r in rows],
                          receipt=ref(target/'receipt.json'))))
