"""Exhaustive finite-universe facet filtering; no parser or open-world proof.

Only independently justified, mutually exclusive categorical facets may be
supplied. Missing contract/query facts are unknown, never negative evidence.
All universe IDs (including unavailable/protected artifacts) remain candidates
unless an internal sound contradiction excludes them. This layer never serves.
"""
from collections.abc import Mapping
from .interpretation_gate import InterpretationEnvelope


class FacetBitsetIndex:
    def __init__(self, universe_ids, facts_by_id):
        if (not isinstance(universe_ids, (tuple, list)) or not universe_ids or
                any(type(x) is not str or not x for x in universe_ids) or
                len(set(universe_ids)) != len(universe_ids)):
            raise ValueError('complete explicit unique universe required')
        if not isinstance(facts_by_id, Mapping) or set(facts_by_id) != set(universe_ids):
            raise ValueError('every universe identity needs a fact slot, possibly empty')
        self.ids = tuple(universe_ids)
        self.all_bits = (1 << len(self.ids)) - 1
        self.known, self.values = {}, {}
        for i, pid in enumerate(self.ids):
            facts = facts_by_id[pid]
            self._check_facts(facts)
            for facet, value in facts.items():
                self.known[facet] = self.known.get(facet, 0) | (1 << i)
                key = (facet, value)
                self.values[key] = self.values.get(key, 0) | (1 << i)

    @staticmethod
    def _check_facts(facts):
        if not isinstance(facts, Mapping) or any(type(k) is not str or not k or
                type(v) is not str or not v for k, v in facts.items()):
            raise ValueError('only justified scalar categorical facts are supported')

    def candidates(self, explicit_query_facts):
        """Internal sound-parser facts only; scores/silence cannot create facts."""
        self._check_facts(explicit_query_facts)
        bits = self.all_bits
        for facet, value in explicit_query_facts.items():
            unknown = self.all_bits ^ self.known.get(facet, 0)
            bits &= unknown | self.values.get((facet, value), 0)
        return frozenset(pid for i, pid in enumerate(self.ids) if bits & (1 << i))

    def envelope(self, explicit_query_facts, *, analysis_contract_sha256,
                 query_sha256, universe_sha256):
        # No facet operation can establish that an outside interpretation is
        # impossible. A separately sound analysis must discharge that obligation.
        return InterpretationEnvelope(self.candidates(explicit_query_facts), True,
                                      analysis_contract_sha256, query_sha256, universe_sha256)
