"""Opt-in missing-requirement gate for one-input stored recognition.

Curated facets are necessary conditions, not a complete equivalence proof.
The selected source stays selected: missing/stale contracts cannot expose a
lower-ranked candidate. No examples, IDs or source facts fill query omissions.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from .requirement_filter import FACETS, contradicts, explicit_facts


class RequiredFacets:
    def __init__(self, contracts):
        self.contracts = {}
        for contract in contracts:
            h = contract['statement_sha256']
            facts, required = contract['facts'], contract['required_facets']
            if (not isinstance(h, str) or len(h) != 64
                    or any(c not in '0123456789abcdef' for c in h)
                    or not isinstance(facts, dict) or not isinstance(required, list)
                    or not required or any(not isinstance(f, str) for f in required)
                    or len(set(required)) != len(required)
                    or not set(required) <= set(facts) <= set(FACETS)
                    or any(not isinstance(v, str) or not v for v in facts.values())):
                raise ValueError('Invalid source-bound required-facet contract')
            normalized = {'facts': copy.deepcopy(facts), 'required_facets': sorted(required)}
            if h in self.contracts and self.contracts[h] != normalized:
                raise ValueError('Conflicting required-facet contracts for one source')
            self.contracts[h] = normalized

    def check(self, text, entry):
        h = hashlib.sha256(entry.statement.encode()).hexdigest()
        contract = self.contracts.get(h)
        parsed = explicit_facts(text)
        result = {'accepted': False, 'statement_sha256': h,
                  'contract': copy.deepcopy(contract), 'query': parsed,
                  'scope': 'necessary curated facets only; not semantic equivalence'}
        if contract is None:
            return dict(result, reason='required_facets_unbound_source')
        required = contract['required_facets']
        missing = sorted(set(required) - set(parsed['facts']))
        uncertain = sorted({s['facet'] for s in parsed['suppressed']} & set(required))
        contradictions = [{'facet': f, 'query': v, 'source': contract['facts'][f]}
                          for f, v in parsed['facts'].items()
                          if f in contract['facts'] and contradicts(f, v, contract['facts'][f])]
        result.update(missing=missing, uncertain=uncertain, contradictions=contradictions)
        reason = ('required_facets_conflict' if parsed['conflicts'] else
                  'required_facets_uncertain' if uncertain else
                  'required_facets_contradiction' if contradictions else
                  'required_facets_missing' if missing else None)
        return dict(result, accepted=reason is None, reason=reason)


class _GuardedApproval:
    def __init__(self, approved, gate, statement):
        self.approved, self.gate, self.statement = approved, gate, statement

    def identity_check(self, entry, candidates, lookup, *, exact, minimum_margin):
        identity = self.approved.identity_check(entry, candidates, lookup,
                                               exact=exact, minimum_margin=minimum_margin)
        # Preserve the established identity rejection and exact-statement route.
        if exact or not identity['accepted']:
            return identity
        guard = self.gate.check(self.statement, entry)
        result = dict(identity, required_facets=guard)
        if not guard['accepted']:
            result.update(accepted=False, reason=guard['reason'])
        return result

    def check(self, entry):
        return self.approved.check(entry)


def answer_with_required_facets(context, query, approved, gate, *, policy=None):
    """Explicit experimental entry point; never enables generated fallback."""
    if approved is None:
        raise ValueError('Required-facet recognition requires an approved library')
    guarded = _GuardedApproval(approved, gate, query.statement)
    if policy is not None:
        from .requirement_filter import answer_with_policy
        return answer_with_policy(context, query, guarded, policy)
    from .answer import answer
    return answer(context, query, approved_library=guarded)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', type=Path)
    parser.add_argument('--approved-library', type=Path, required=True)
    parser.add_argument('--contracts', type=Path, required=True)
    args = parser.parse_args()
    document = json.loads(args.contracts.read_text())
    if document.get('schema_version') != 1:
        raise ValueError('Unsupported required-facet schema')
    gate = RequiredFacets(document['contracts'])
    from .approved_library import load_context
    from .records import Problem
    context, approved = load_context(args.approved_library)
    result = answer_with_required_facets(context, Problem.from_dict(json.loads(args.query.read_text())),
                                         approved, gate)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
