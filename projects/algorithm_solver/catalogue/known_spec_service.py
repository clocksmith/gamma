"""Exact known-spec metadata/artifact CLI; no model, candidate execution or server.

Configuration and receipt-verifier outputs are supplied by the trusted operator,
not by a request. A pinned config authenticates bytes, not the operator's authority.
"""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

from .catalogue import digest, validate
from . import boundary_policy
from .materialize import read_source
from .retrieval import KnownCatalogue


def _pinned_json(spec):
    data = Path(spec['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError('configuration artifact hash mismatch')
    return json.loads(data)


def _exact_fields(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= set(value) or set(value) - set(required) - set(optional):
        raise ValueError('unexpected or missing service fields')


def _strict_spec(spec):
    _exact_fields(spec, ('path', 'sha256'))
    if (not isinstance(spec['path'], str) or not Path(spec['path']).is_absolute() or
            not isinstance(spec['sha256'], str) or not re.fullmatch(r'[0-9a-f]{64}', spec['sha256'])):
        raise ValueError('invalid pinned metadata descriptor')
    with Path(spec['path']).open('rb') as stream:
        raw = stream.read(32 * 1024 * 1024 + 1)
    if len(raw) > 32 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != spec['sha256']:
        raise ValueError('bounded pinned service metadata mismatch')
    def unique(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('duplicate service metadata field')
            value[key] = item
        return value
    return json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite service metadata')))


def _boundary_snapshot(gate):
    _exact_fields(gate, ('schema', 'artifact_paths', 'trusted_hashes'))
    if gate['schema'] != 'gamma.boundary-gate-config.v1':
        raise ValueError('unsupported boundary gate configuration')
    _exact_fields(gate['artifact_paths'], boundary_policy.ARTIFACTS)
    raw = {}
    for name, path in gate['artifact_paths'].items():
        if not isinstance(path, str) or not Path(path).is_absolute():
            raise ValueError('absolute operator metadata paths required')
        with Path(path).open('rb') as stream:
            raw[name] = stream.read(boundary_policy.MAX_METADATA_BYTES + 1)
    return boundary_policy.validate_policy(raw, gate['trusted_hashes'])


def rebind_boundary_universe(old_universe, old_catalogue, receipts, new_universe,
                             gate, *, predecessor_catalogue_sha256):
    """Metadata-only monotone protection successor; no source opens/promotions.

    Caller authenticates raw predecessor bytes separately; the canonical digest
    here is an additional explicit provenance anchor, not a replacement receipt.
    Every qualified implementation and all receipts remain byte-value identical.
    """
    validate(old_universe, old_catalogue, receipts)
    if digest(old_catalogue) != predecessor_catalogue_sha256:
        raise ValueError('predecessor canonical catalogue anchor mismatch')
    boundary = _boundary_snapshot(gate)
    raw = Path(gate['artifact_paths']['universe']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != boundary.universe_sha256 or json.loads(raw) != new_universe:
        raise ValueError('new universe differs from independently bound boundary')
    if (set(new_universe['eligible_problem_ids']) != set(old_universe['eligible_problem_ids']) or
            not set(old_universe['protected_problem_ids']) <= set(new_universe['protected_problem_ids'])):
        raise ValueError('identity denominator changed or protection weakened')
    result = copy.deepcopy(old_catalogue)
    result['universe_sha256'] = digest(new_universe)
    for row in result['problems']:
        if row['problem_id'] not in boundary.protected:
            continue
        for language, impl in row['implementations'].items():
            if impl['status'] == 'qualified':
                raise ValueError('newly protected identity conflicts with qualified source')
            row['implementations'][language] = {'status': 'protected',
                'reason': 'Reserved by independently reviewed metadata boundary; no source access.',
                'provenance': {'previous_slot_sha256': digest(impl),
                    'previous_catalogue_sha256': predecessor_catalogue_sha256,
                    'boundary_policy_sha256': boundary.policy_sha256}}
    summary = validate(new_universe, result, receipts)
    return result, copy.deepcopy(receipts), {'schema': 'gamma.catalogue-boundary-rebind.v1',
        'predecessor_catalogue_sha256': predecessor_catalogue_sha256,
        'predecessor_universe_sha256': digest(old_universe),
        'successor_universe_sha256': digest(new_universe),
        'boundary_policy_sha256': boundary.policy_sha256,
        'protected_before': len(old_universe['protected_problem_ids']),
        'protected_after': len(boundary.protected), 'authorized_acquisition': len(boundary.authorized),
        'unknown_metadata_only': len(boundary.unknown), 'receipts_preserved': len(receipts),
        'qualified_implementations_unchanged': True, 'source_payload_reads': 0,
        'candidate_executions': 0, 'summary': summary}


class KnownSpecService:
    def __init__(self, config):
        config = copy.deepcopy(config)
        if config.get('schema') not in ('gamma.known-spec-service.v1', 'gamma.known-spec-service.v2'):
            raise ValueError('unsupported service configuration')
        self._version = config['schema']
        self._boundary = None
        if self._version == 'gamma.known-spec-service.v2':
            _exact_fields(config, ('schema', 'universe', 'catalogue', 'verified_receipts'), ('source_access',))
            for name in ('universe', 'catalogue', 'verified_receipts'):
                _strict_spec(config[name])
        self._universe = _pinned_json(config['universe'])
        self.catalogue = KnownCatalogue(self._universe, _pinned_json(config['catalogue']),
                                        _pinned_json(config['verified_receipts']))
        self._source = None
        source = config.get('source_access')
        if source is not None and self._version == 'gamma.known-spec-service.v2':
            self._configure_v2(config, source)
            return
        if source is not None:
            aliases = _pinned_json(source['aliases'])
            locators = _pinned_json(source['locators'])
            if (aliases.get('schema') != 'gamma.numeric-id-alias-map.v1' or
                    aliases.get('to_universe_sha256') != config['universe']['sha256'] or
                    aliases.get('from_universe_sha256') != source['development_universe_sha256']):
                raise ValueError('source identity universe mismatch')
            mapping = aliases['aliases']
            if (not isinstance(mapping, dict) or len(set(mapping.values())) != len(mapping) or
                    any(not isinstance(k, str) or not isinstance(v, str) or
                        not k.startswith('development400:') or not v.startswith('leetcode:') or
                        not k.split(':', 1)[1].isascii() or not k.split(':', 1)[1].isdigit() or
                        k.split(':', 1)[1] != v.split(':', 1)[1] for k, v in mapping.items())):
                raise ValueError('only exact permitted development numeric aliases are supported')
            access_policy = _pinned_json(source['access_policy'])
            if (access_policy.get('schema') != 'gamma.all4081-source-access-policy.v1' or
                    access_policy.get('new_source_access_authorized') is not False or
                    access_policy.get('source_publication_authorized') is not False or
                    set(access_policy.get('authorized_existing_source_problem_ids', [])) != set(mapping.values())):
                raise ValueError('mandatory development source-access policy mismatch')
            authorized = source['authorized_problem_ids']
            if (not isinstance(authorized, list) or any(not isinstance(x, str) for x in authorized) or
                    len(authorized) != len(set(authorized)) or not set(authorized) <= set(mapping.values()) or
                    not set(authorized) <= set(self._universe['eligible_problem_ids']) or
                    set(authorized) & set(self._universe['protected_problem_ids'])):
                raise ValueError('source authorization must be a nonprotected development subset')
            roots = source['source_roots']
            if not isinstance(roots, list) or not roots:
                raise ValueError('explicit pinned source roots required')
            for root in roots:
                if (not isinstance(root, str) or not root.startswith('/') or root == '/' or
                        any(p in ('', '.', '..') for p in root[1:].split('/'))):
                    raise ValueError('invalid source root')
            if locators.get('schema') != 'gamma.dual.source-locators.v1':
                raise ValueError('unsupported source locator manifest')
            self._source = (source, {v: k for k, v in mapping.items()}, locators['problems'])

    def _configure_v2(self, config, source):
        _exact_fields(source, ('schema', 'boundary_gate', 'locators', 'authorized_problem_ids', 'source_roots'),
                      ('aliases', 'development_universe_sha256'))
        if source['schema'] != 'gamma.known-spec-source-access.v2':
            raise ValueError('explicit source-access version required')
        gate = _strict_spec(source['boundary_gate'])
        boundary = _boundary_snapshot(gate)
        if (boundary.universe_sha256 != config['universe']['sha256'] or
                boundary.protected != frozenset(self._universe['protected_problem_ids'])):
            raise ValueError('service and source boundary universe differ')
        authorized = source['authorized_problem_ids']
        if (not isinstance(authorized, list) or any(not isinstance(x, str) for x in authorized) or
                len(set(authorized)) != len(authorized) or not set(authorized) <= boundary.authorized):
            raise ValueError('explicit source subset must be boundary-authorized')
        mapping = {}
        if 'aliases' in source:
            aliases = _strict_spec(source['aliases'])
            if (aliases.get('schema') != 'gamma.numeric-id-alias-map.v1' or
                    aliases.get('to_universe_sha256') != boundary.universe_sha256 or
                    aliases.get('from_universe_sha256') != source.get('development_universe_sha256') or
                    aliases.get('access_policy_sha256') != boundary.policy_sha256):
                raise ValueError('legacy alias universe/policy binding mismatch')
            mapping = aliases.get('aliases')
            if (not isinstance(mapping, dict) or set(mapping.values()) != boundary.existing or
                    len(set(mapping.values())) != len(mapping) or
                    any(not isinstance(k, str) or not isinstance(v, str) or
                        not re.fullmatch(r'development400:[1-9][0-9]*', k, re.ASCII) or
                        v != 'leetcode:' + k.split(':')[1] for k, v in mapping.items())):
                raise ValueError('legacy aliases must be explicit exact existing numeric identities')
        elif 'development_universe_sha256' in source:
            raise ValueError('development universe requires explicit aliases')
        roots = source['source_roots']
        if not isinstance(roots, list) or not roots or len(set(roots)) != len(roots):
            raise ValueError('unique explicit source roots required')
        for root in roots:
            if (not isinstance(root, str) or not root.startswith('/') or root == '/' or
                    any(p in ('', '.', '..') for p in root[1:].split('/'))):
                raise ValueError('invalid source root')
        locators = _strict_spec(source['locators'])
        _exact_fields(locators, ('schema', 'problems'))
        if locators['schema'] != 'gamma.dual.source-locators.v1' or not isinstance(locators['problems'], dict):
            raise ValueError('unsupported source locator manifest')
        keys = {}
        for key, languages in locators['problems'].items():
            pid = mapping.get(key, key)
            if (not isinstance(pid, str) or not re.fullmatch(r'leetcode:[1-9][0-9]*', pid, re.ASCII) or
                    pid not in authorized or pid in keys):
                raise ValueError('unknown, duplicated or unauthorized global source locator identity')
            if (not isinstance(languages, dict) or not languages or
                    not set(languages) <= {'javascript', 'python'} or
                    any(not isinstance(path, str) or not path.startswith('/') for path in languages.values())):
                raise ValueError('invalid language source locator')
            keys[pid] = key
        self._boundary = (source['boundary_gate'], gate)
        self._source = (source, keys, locators['problems'])

    @classmethod
    def from_config(cls, path, sha256):
        return cls(_strict_spec({'path': str(path), 'sha256': sha256}))

    def request(self, problem_id, *, language=None, include_source=False):
        """Only identity, consumer language and artifact opt-in are request inputs."""
        value = self.catalogue.retrieve(problem_id)
        value['clarification_questions'] = []
        if value['status'] != 'matched':
            return value
        if language is None:
            if include_source:
                return self._abstain('source_requires_consumer_language')
            return value
        if language not in ('javascript', 'python'):
            return self._abstain('unsupported_consumer_language')
        selection = self.catalogue.select_language(value, language)
        if selection['status'] != 'selected':
            return self._abstain(selection['reason'])
        if not include_source:
            value['consumer_selection'] = selection
            return value
        if self._source is None:
            return self._abstain('source_policy_required')
        source, aliases, locators = self._source
        if (problem_id not in source['authorized_problem_ids'] or
                problem_id in self._universe['protected_problem_ids'] or problem_id not in aliases):
            return self._abstain('source_not_authorized')
        if self._boundary is not None:
            try:
                # Re-read pinned locator/alias metadata; no request-controlled paths.
                locators = _strict_spec(source['locators'])['problems']
                if 'aliases' in source:
                    _strict_spec(source['aliases'])
            except (OSError, ValueError, KeyError, TypeError):
                return self._abstain('source_metadata_changed')
        path = locators.get(aliases[problem_id], {}).get(language)
        if not isinstance(path, str):
            return self._abstain('source_locator_unavailable')
        roots = [root for root in source['source_roots'] if path.startswith(root + '/')]
        if not roots:
            return self._abstain('source_outside_pinned_roots')
        root = max(roots, key=len)
        impl = selection['implementation']
        locator = {'problem_id': problem_id, 'language': language,
                   'relative_path': path[len(root) + 1:], 'universe_sha256': digest(self._universe),
                   'source_sha256': impl['source_sha256'], 'receipt_sha256': impl['receipt_sha256']}
        policy = {'authorized_problem_ids': source['authorized_problem_ids'],
                  'protected_problem_ids': self._universe['protected_problem_ids'],
                  'universe_sha256': digest(self._universe), 'source_root': root}
        try:
            if self._boundary is not None:
                gate_spec, gate = self._boundary
                if _strict_spec(gate_spec) != gate:
                    raise ValueError('boundary gate changed')
                # This gate is immediately before the actual source opener and
                # independently denies reserved/unknown even with a valid receipt.
                boundary_policy.authorize_before_open(problem_id, gate['artifact_paths'],
                    gate['trusted_hashes'], language=language, payload_kind='source')
            data = read_source(selection, locator, policy)
            text = data.decode('utf-8')
        except (OSError, ValueError, UnicodeError, KeyError, TypeError):
            return self._abstain('source_materialization_failed')
        value['consumer_selection'] = selection
        value['artifact'] = {'status': 'materialized', 'language': language, 'source_utf8': text,
                             'source_sha256': impl['source_sha256'], 'bytes': len(data),
                             'evidence_scope': 'exact receipt-bound bytes only; not executed or query-public verified'}
        return value

    @staticmethod
    def _abstain(reason):
        return {'status': 'abstain', 'reason': reason, 'clarification_questions': []}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--config-sha256', required=True)
    parser.add_argument('--problem-id', required=True)
    parser.add_argument('--language', choices=('javascript', 'python'))
    parser.add_argument('--include-source', action='store_true')
    args = parser.parse_args(argv)
    try:
        service = KnownSpecService.from_config(args.config, args.config_sha256)
        value = service.request(args.problem_id, language=args.language, include_source=args.include_source)
    except (OSError, ValueError, KeyError, TypeError):
        value = KnownSpecService._abstain('invalid_service_configuration')
    print(json.dumps(value, sort_keys=True))
    return 0 if value['status'] == 'matched' else 2


if __name__ == '__main__':
    raise SystemExit(main())
