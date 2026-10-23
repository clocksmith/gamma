"""Named frozen codec imports; import opens no population artifacts."""
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIT = HERE.parent


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


prior = module('fraction_primal_codec', LIT / 'length-sensitive-fraction-v1/backend.py')
analyze, dual, sha, write, measure = prior.analyze, prior.dual, prior.sha, prior.write, prior.measure
CERT_KEYS = ('numerator', 'denominator', 'integer_lower_bound', 'path_numerators', 'top_capacity_numerator')


def inputs(c, work, cohort):
    """Caller must verify contract hashes before entering this fit-only loader."""
    import json
    texts = json.loads((work / c['cohorts'][cohort] / 'fit-sources.json').read_text())
    assert set(texts) == set(map(str, c['fit_ids'])) and len(texts) == 300
    assert all(type(t) is str and t for t in texts.values())
    assert set(''.join(texts.values())) <= set(dual.ALPHABET)
    proof = json.loads((LIT / 'binding-descent-v1/evidence/results.json').read_text())
    receipts = [a for a in proof['arms'] if a['width'] == 8 and a['arm'] == ('control' if cohort == 'R' else 'scope_joint')]
    assert len(receipts) == 1
    for pid, text in texts.items():
        assert receipts[0]['qualification'][pid]['passed'] is True
        assert receipts[0]['per_problem'][pid]['source_sha256'] == analyze.sha(text.encode())
    public = json.loads((LIT / c['parent_evidence']).read_text())
    private = json.loads((work / c['parent_private_results']).read_text())
    assert public['complete'] is True and private['complete'] is True
    assert public['validation_loaded'] is False and private['validation_loaded'] is False
    assert sha(work / c['parent_private_results']) == public['private_results_sha256']
    pa = next(a for a in public['arms'] if a['cohort'] == cohort)
    raw = next(a for a in private['arms'] if a['cohort'] == cohort)
    assert raw['complete'] is True and raw['validation_loaded'] is False
    assert pa['fit_source_sha256'] == raw['fit_source_sha256'] == sha(work / c['cohorts'][cohort] / 'fit-sources.json')
    qpath = work / c['parent_q'][cohort]; seedpath = work / c['parent_seed'][cohort]
    assert pa['certificate']['q_sha256'] == raw['optimization']['certificate']['q_sha256'] == sha(qpath)
    for key in CERT_KEYS:
        assert pa['certificate'][key] == raw['optimization']['certificate'][key]
    assert pa['witnesses']['seed']['dictionary_sha256'] == raw['witnesses']['seed']['dictionary_sha256'] == sha(seedpath)
    return texts, json.loads(seedpath.read_text()), json.loads(qpath.read_text()), pa
