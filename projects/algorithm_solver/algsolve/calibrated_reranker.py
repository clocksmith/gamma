"""Load a development calibration only with its exact inputs and runtime."""
import hashlib
import json
from pathlib import Path
import subprocess

from .records import LANE_ROOT
from .rerank import DopplerReranker
from .rerank_recognition import calibrate, digest, load_rows


def load(directory: Path, cli: Path, model_dir: Path):
    contract = json.loads((directory/'contract.json').read_text())
    calibration = json.loads((directory/'calibration.json').read_text())
    rows = load_rows(directory/'dev.jsonl', contract['dev_queries'])
    if (calibration['binding'] != digest(contract) or calibration['dev_rows_sha256'] != digest(rows)
            or calibration['thresholds'] != calibrate(rows, contract['dev_queries'])):
        raise ValueError('Calibration differs from its complete development fit')
    for relative, expected in contract['files'].items():
        path = (LANE_ROOT/relative).resolve()
        path.relative_to(LANE_ROOT.resolve())
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Calibration input changed: {relative}')
    reranker = DopplerReranker(cli, model_dir, runtime_config=contract['runtime_config'])
    if (reranker.manifest_sha256 != contract['model_manifest_sha256'] or reranker.model_id != contract['model_id']
            or reranker.runtime_config_sha256 != contract['runtime_config_sha256']):
        raise ValueError('Reranker model or execution config differs from calibration')
    root = reranker.cli.parents[2]
    revision = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    if revision != contract['runtime_revision'] or dirty:
        raise ValueError('Doppler runtime differs from calibration')
    return reranker, calibration['thresholds']
