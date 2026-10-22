"""Time the frozen preparation steps by rerunning them into temporary outputs.

Each rerun must reproduce its frozen output; the timing is then reported as preparation
cost, separate from search. Label extraction timing is supplied from its run on 128.
Usage: python3 measure_preparation.py <preparation.json> <label-extraction-seconds>
"""
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def timed(command):
    start = time.monotonic()
    subprocess.run(command, check=True, capture_output=True)
    return time.monotonic() - start


def main():
    out, label_seconds = Path(sys.argv[1]), float(sys.argv[2])
    if out.exists():
        raise SystemExit(f'refusing to overwrite {out}')
    with tempfile.TemporaryDirectory() as tmp:
        pool = Path(tmp) / 'pool.json'
        build = timed([sys.executable, '-I', '-B', str(ROOT / 'designed/build_pool.py'), '--output', str(pool)])
        if pool.read_bytes() != (ROOT / 'designed/pool.json').read_bytes():
            raise SystemExit('builder rerun did not reproduce designed/pool.json')
        receipt = Path(tmp) / 'receipt.json'
        qualify = timed(['node', str(ROOT / 'designed/qualify_components.cjs'), str(ROOT / 'designed/pool.json'), str(receipt)])
        frozen = json.loads((ROOT / 'designed/qualification-mars.json').read_text())
        if json.loads(receipt.read_text())['results'] != frozen['results']:
            raise SystemExit('qualification rerun differs from the frozen Mars receipt')
    pool_data = json.loads((ROOT / 'designed/pool.json').read_text())
    result = {'schema': 'gamma.matched80.preparation.v1',
              'designed_pool': {'pieces': pool_data['counts'], 'excluded': pool_data['excluded_counts'], 'builder_seconds': build,
                                'authoring': 'Pieces and contract cards were assistant-authored and owner-approved; authoring effort is not a measured quantity.'},
              'component_qualification': {'checks': frozen['checks_total'], 'summary': frozen['summary'], 'seconds_on_mars': qualify},
              'label_extraction': {'seconds_on_jupiter': label_seconds},
              'note': 'Timed by rerunning frozen steps after the freeze; each rerun reproduced its frozen output. Mined candidates are generated inside the search.'}
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
