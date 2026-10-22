"""Compute supplement for sixbit-v1 on Jupiter (FREEZE-jupiter.md).

Runs run.py's unchanged run_job() for the declared jobs with the supplement's limits,
after checking the pinned files and the pinned scipy and numpy versions. Output is a
separate run; run-v1 on Mars remains the frozen record."""
import argparse
import json
import platform
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy
import scipy

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import run


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default=str(ROOT / 'run-jupiter-v1'))
    args = parser.parse_args()
    supplement = json.loads((ROOT / 'contract-jupiter.json').read_text())
    for rel, digest in supplement['inputs'].items():
        if run.sha((ROOT / rel).read_bytes()) != digest:
            raise SystemExit(f'pinned input changed: {rel}')
    versions = {'scipy': scipy.__version__, 'numpy': numpy.__version__}
    if versions != supplement['versions']:
        raise SystemExit(f'versions {versions} differ from {supplement["versions"]}')
    out = Path(args.output)
    if out.exists():
        raise SystemExit(f'refusing existing output {out}')
    out.mkdir()
    limits = dict(supplement['limits'], output=str(out))
    run.write(out / 'environment.json', {
        'python': sys.version, **versions, 'platform': platform.platform(), 'host': platform.node(),
        'workers': limits['workers'], 'jobs': supplement['jobs'], 'limits': supplement['limits'],
        'peak_rss_unit': 'KiB: run.py stores Linux ru_maxrss under peak_rss_bytes',
        'highs_threads': supplement['threads']})
    with ProcessPoolExecutor(limits['workers']) as pool:
        for name, seconds in pool.map(run.run_job, supplement['jobs'], [limits] * len(supplement['jobs'])):
            print(json.dumps({'job': name, 'seconds': seconds}), flush=True)


if __name__ == '__main__':
    main()
