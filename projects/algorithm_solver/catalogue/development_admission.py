"""Downstream admission of exact qualified sources for development research.

Inventory generation remains read-only. This stage rechecks source bytes,
repository license applicability and conservative host-policy observations.
It assigns no splits, opens no cases, creates no correctness qualification and
does not admit browser guides. Historical fitting authority remains separate.
"""
import argparse
from collections import Counter
import copy
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess

from .catalogue import BINDINGS, digest
from .guide_admission import save_snapshot
from .known_spec_service import KnownSpecService, _strict_spec

ROOT = Path(__file__).resolve().parents[3]
JS_REVIEW = Path(__file__).with_name('source_host_review.cjs')
PY_REVIEW = ROOT / 'projects/algorithm_solver/literals/python-source-rendering-v1/render.py'
sha = lambda raw: hashlib.sha256(raw).hexdigest()


@lru_cache(maxsize=512)
def nested_license(repository, commit, directory):
    names = subprocess.check_output(['git', 'ls-tree', '--name-only', commit + ':' + directory],
                                    cwd=repository, stderr=subprocess.DEVNULL, text=True).splitlines()
    return any(name.lower().startswith(('license', 'copying', 'code_license')) for name in names)


def repository_license(repository, evidence, pid, language, source):
    """Verify actual Git bytes; an evidence 'passed' field is never consumed."""
    commit, path = evidence.get('repository_commit'), evidence.get('source_path')
    if (evidence.get('schema') != 'gamma.exact-repository-license-reference.v1' or
            evidence.get('license') != 'MIT' or not isinstance(commit, str) or
            not re.fullmatch(r'[0-9a-f]{40}', commit) or not isinstance(path, str) or
            not path.startswith('projects/algorithm_solver/catalogue/authored/') or
            '..' in Path(path).parts or '\n' in path or
            Path(path).suffix != ('.js' if language == 'javascript' else '.py') or
            Path(path).stem != pid.split(':')[1] or evidence.get('license_path') != 'LICENSE'):
        return False
    def read(relative, maximum):
        ref = commit + ':' + relative
        size = int(subprocess.check_output(['git', 'cat-file', '-s', ref], cwd=repository, stderr=subprocess.DEVNULL))
        if not 0 < size <= maximum:
            raise ValueError('bounded Git artifact required')
        return subprocess.check_output(['git', 'show', ref], cwd=repository, stderr=subprocess.DEVNULL)
    try:
        if any(nested_license(str(repository), commit, str(parent))
               for parent in Path(path).parents if str(parent) != '.'):
            return False  # A narrower license requires its own reviewed route.
        license_raw, source_raw = read('LICENSE', 65536), read(path, 65536)
    except (subprocess.CalledProcessError, ValueError):
        return False
    return (license_raw.startswith(b'MIT License\n') and
            sha(license_raw) == evidence.get('license_sha256') and
            source_raw == source.encode() and sha(source_raw) == evidence.get('source_sha256'))


def review_sources(sources):
    """Execute trusted parsers only; never execute the supplied source programs."""
    spec = importlib.util.spec_from_file_location('development_python_preflight', PY_REVIEW)
    python = importlib.util.module_from_spec(spec); spec.loader.exec_module(python)
    js, result = {}, {}
    for key, (language, text) in sources.items():
        if language == 'javascript':
            js[key] = text
        else:
            reason = python.unsafe_reason(text, python.parse(text))
            result[key] = {'unsupported': [] if reason is None else [reason],
                           'policy': 'existing_conservative_python_rendering_preflight'}
    if js:
        process = subprocess.run(['node', str(JS_REVIEW)], input=json.dumps(js), text=True,
                                 capture_output=True, timeout=90, check=True)
        observed = json.loads(process.stdout)
        if set(observed) != set(js):
            raise ValueError('incomplete host observations')
        result.update(observed)
    return result


def admit(queue, service, evidence, *, repository=ROOT,
          check_license=repository_license, check_hosts=review_sources):
    """Produce a successor inventory with independently scoped development results."""
    result = copy.deepcopy(queue)
    if result['summary']['development_corpus_admitted'] or result.get('development_admission'):
        raise ValueError('admit a fresh inventory, never accumulate admission flags')
    licenses = {}
    for record in evidence:
        if record.get('kind') != 'license':
            continue
        key = (record['problem_id'], record['language'])
        if key in licenses:
            raise ValueError('ambiguous license references')
        licenses[key] = record
    pending, sources, opened, source_bytes = {}, {}, 0, 0
    for row in result['problems']:
        for language, slot in row['implementations'].items():
            reasons = []
            slot['development_corpus_admitted'] = False
            if row['permission'] != 'source_access_authorized': reasons.append('source_permission_not_authorized')
            if not slot['qualification']['receipt_binding_checked']: reasons.append('qualification_not_established')
            if not any(r['qualification_join'] == 'exact_existing_canonical_receipt'
                       for r in slot.get('authoring_variants', {}).get('records', [])):
                reasons.append('complete_source_contract_variant_join_missing')
            license_record = licenses.get((row['problem_id'], language))
            if not license_record or license_record['bindings'] != slot['bindings']:
                reasons.append('exact_repository_license_reference_missing')
            slot['development_blockers'] = reasons
            if reasons:
                continue
            value = service.request(row['problem_id'], language=language, include_source=True)
            opened += 1
            artifact = value.get('artifact', {}); impl = value.get('consumer_selection', {}).get('implementation', {})
            text = artifact.get('source_utf8')
            if (artifact.get('status') != 'materialized' or not isinstance(text, str) or
                    sha(text.encode()) != slot['bindings']['source_sha256'] or
                    {key: impl.get(key) for key in BINDINGS} != slot['bindings'] or
                    impl.get('receipt_sha256') != slot['qualification']['receipt_sha256']):
                raise ValueError('live source/qualification binding drift')
            if not check_license(repository, license_record['evidence'], row['problem_id'], language, text):
                reasons.append('repository_license_verification_failed')
                continue
            interface = slot['interface']
            if (interface.get('entrypoint') != 'solve' or interface.get('arguments') != 'ordered-positional' or
                    digest(interface) != slot['bindings']['interface_sha256']):
                reasons.append('qualified_call_interface_unsupported')
                continue
            key = row['problem_id'] + '/' + language
            source_bytes += len(text.encode())
            if source_bytes > 32 * 1024**2:
                raise ValueError('development source byte budget exceeded')
            pending[key] = (slot, license_record, language)
            sources[key] = (language, text)
    observations = check_hosts(sources)
    if set(observations) != set(sources):
        raise ValueError('incomplete development host review')
    for key, (slot, license_record, language) in pending.items():
        observation = observations[key]
        if not isinstance(observation.get('unsupported'), list):
            raise ValueError('explicit host-policy findings required')
        slot['development_host_review'] = observation
        slot['development_blockers'].extend('host_policy:' + reason for reason in observation['unsupported'])
        if slot['development_blockers']:
            continue
        slot['development_corpus_admitted'] = True
        slot['development_license'] = {'verified_reference': {
            'record_sha256': digest(license_record), 'bindings': dict(slot['bindings'])},
                                       'source_publication_authorized': False}
        slot['development_adapter'] = {'kind': 'existing_qualified_solve_interface', 'language': language,
            'interface_sha256': slot['bindings']['interface_sha256'],
            'qualified_runtime_sha256': slot['bindings']['runtime_sha256'], 'browser_adapter': False}
    counts = Counter(language for row in result['problems'] for language, slot in row['implementations'].items()
                     if slot['development_corpus_admitted'])
    result['summary']['development_corpus_admitted'] = sum(counts.values())
    result['summary']['development_admitted_by_language'] = dict(counts)
    result['summary']['development_admitted_pairs'] = sum(
        all(slot['development_corpus_admitted'] for slot in row['implementations'].values()) for row in result['problems'])
    result['summary']['development_blockers'] = dict(Counter(reason for row in result['problems']
        for slot in row['implementations'].values() for reason in slot['development_blockers']))
    result['development_admission'] = {'schema': 'gamma.exact-development-source-admission.v1',
        'source_payload_reads': opened, 'candidate_executions': 0, 'qualification_created': False,
        'browser_guides_admitted': 0, 'splits_assigned': False, 'fitting_population_frozen': False,
        'scope': 'Exact existing qualified sources, repository license bytes and conservative static host policy. Existing runtime-qualified contract only; not universal proof, browser admission or new source publication authority.'}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = _strict_spec({'path': str(args.config), 'sha256': args.config_sha256})
    if set(config) != {'inventory', 'service', 'license_evidence'}:
        raise ValueError('pinned inventory, service and license evidence required')
    queue = _strict_spec(config['inventory']); licenses = _strict_spec(config['license_evidence'])
    if queue['inputs']['service_sha256'] != config['service']['sha256']:
        raise ValueError('inventory/service mismatch')
    service = KnownSpecService.from_config(config['service']['path'], config['service']['sha256'])
    result = admit(queue, service, licenses)
    result['development_admission']['inputs'] = config
    result['development_admission']['code_sha256'] = {
        p.name: sha(p.read_bytes()) for p in (Path(__file__), JS_REVIEW, PY_REVIEW)}
    save_snapshot(args.output, result)
    print(json.dumps({key: result['summary'][key] for key in
                      ('development_corpus_admitted', 'development_admitted_by_language', 'development_admitted_pairs')}))


if __name__ == '__main__':
    main()
