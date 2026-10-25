"""Exact known-spec metadata/artifact CLI; no model, candidate execution or server.

Configuration and receipt-verifier outputs are supplied by the trusted operator,
not by a request. A pinned config authenticates bytes, not the operator's authority.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from .catalogue import digest
from .materialize import read_source
from .retrieval import KnownCatalogue


def _pinned_json(spec):
    data = Path(spec['path']).read_bytes()
    if hashlib.sha256(data).hexdigest() != spec['sha256']:
        raise ValueError('configuration artifact hash mismatch')
    return json.loads(data)


class KnownSpecService:
    def __init__(self, config):
        config = copy.deepcopy(config)
        if config.get('schema') != 'gamma.known-spec-service.v1':
            raise ValueError('unsupported service configuration')
        self._universe = _pinned_json(config['universe'])
        self.catalogue = KnownCatalogue(self._universe, _pinned_json(config['catalogue']),
                                        _pinned_json(config['verified_receipts']))
        self._source = None
        source = config.get('source_access')
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

    @classmethod
    def from_config(cls, path, sha256):
        return cls(_pinned_json({'path': str(path), 'sha256': sha256}))

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
            data = read_source(selection, locator, policy)
            text = data.decode('utf-8')
        except (OSError, ValueError, UnicodeError):
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
