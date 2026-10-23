"""Export replayed numeric evidence, excluding sources, dictionaries and plans."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def export(folder):
    raw = (folder / 'report.json').read_bytes()
    result = json.loads(raw)
    assert result['representation'] == 'separate_structured_2c'
    assert result['fresh_case_executions'] == 0
    # The independent reporter emits only these metadata fields. Fail closed
    # if execution later adds source-bearing payloads to the public schema.
    assert set(result) == {
        'arms', 'contract_sha256', 'default_unchanged', 'flat_M1_promotion_allowed',
        'fresh_case_executions', 'predictions', 'representation', 'seconds',
        'selected_structured_candidate', 'source_qualification_reused',
        'source_receipt_sha256'}
    forbidden = {'sources', 'source', 'texts', 'dictionary', 'keys', 'plans',
                 'pool', 'constructors', 'packet', 'ids_sequence', 'trace'}
    def audit(value):
        if isinstance(value, dict):
            assert not forbidden.intersection(value)
            for child in value.values():
                audit(child)
        elif isinstance(value, list):
            for child in value:
                audit(child)
    audit(result)
    receipt = json.loads((folder / 'supervisor-receipt.json').read_text())
    result.update(schema='gamma.structured-stacking.evidence.v1',
                  private_report_sha256=hashlib.sha256(raw).hexdigest(),
                  private_results_sha256=hashlib.sha256((folder / 'results.json').read_bytes()).hexdigest(),
                  supervisor={k: receipt[k] for k in
                              ('elapsed', 'exit_code', 'outer_timeout', 'complete', 'promotion_allowed')})
    c = json.loads((HERE / 'contract.json').read_text())
    result['offline_source_inventory_bytes'] = {
        rel: (HERE.parent / rel).stat().st_size for rel in c['code_hashes']}
    result['runtime_binary_inventory_bytes'] = {
        path: Path(path).stat().st_size for path in c['runtime_files']}
    result['installed_runtime_footprint_measured'] = False
    out = HERE / 'evidence'
    out.mkdir(exist_ok=True)
    (out / 'results.json').write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    export(parser.parse_args().run)
