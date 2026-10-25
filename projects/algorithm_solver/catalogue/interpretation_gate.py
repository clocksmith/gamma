"""Conservative finite interpretation refinement, not a natural-language parser.

Soundness is conditional on a separately trusted analyzer supplying a COMPLETE
sound overapproximation and sound contradiction verdicts. Embedding top-k lists,
score margins, self-reported proof flags and user request fields do not establish
those premises. No production analyzer is certified by this module.
"""
from dataclasses import dataclass
from enum import Enum
from collections.abc import Mapping
from .catalogue import hash_value


class Facet(Enum):
    SATISFIED = 'satisfied'
    VIOLATED = 'violated'
    UNKNOWN = 'unknown'


@dataclass(frozen=True)
class InterpretationEnvelope:
    identities: frozenset
    outside_catalogue_possible: bool
    analysis_contract_sha256: str
    query_sha256: str
    universe_sha256: str

    def __post_init__(self):
        if (type(self.identities) is not frozenset or
                any(type(x) is not str or not x for x in self.identities) or
                type(self.outside_catalogue_possible) is not bool or
                not all(hash_value(x) for x in (self.analysis_contract_sha256,
                                                self.query_sha256, self.universe_sha256))):
            raise ValueError('invalid trusted interpretation envelope')


def refine(envelope, verdicts, *, outside_verdict=Facet.UNKNOWN):
    """Keep all unknown/satisfied interpretations; remove only sound violations.

    Verdicts are INTERNAL analyzer outputs under the envelope's exact contract,
    not assertions accepted from a user or an embedding model. Missing verdicts
    mean UNKNOWN. A refinement can never add identities or restore outside risk.
    """
    if not isinstance(envelope, InterpretationEnvelope) or not isinstance(verdicts, Mapping):
        raise TypeError('typed envelope and internal verdict map required')
    if any(key not in envelope.identities for key in verdicts):
        raise ValueError('refinement cannot introduce or silently substitute identities')
    if any(type(value) is not Facet for value in verdicts.values()) or type(outside_verdict) is not Facet:
        raise ValueError('explicit three-valued facets required')
    kept = frozenset(pid for pid in envelope.identities if verdicts.get(pid, Facet.UNKNOWN) is not Facet.VIOLATED)
    return InterpretationEnvelope(kept,
        envelope.outside_catalogue_possible and outside_verdict is not Facet.VIOLATED,
        envelope.analysis_contract_sha256, envelope.query_sha256, envelope.universe_sha256)


def identity_decision(envelope):
    """Conditional singleton rule; no language/source-availability tie breaking."""
    if not isinstance(envelope, InterpretationEnvelope):
        raise TypeError('trusted interpretation envelope required')
    if envelope.outside_catalogue_possible:
        reason = 'outside_catalogue_interpretation_possible'
    elif not envelope.identities:
        reason = 'inconsistent_or_empty_interpretation_envelope'
    elif len(envelope.identities) != 1:
        reason = 'semantic_identity_ambiguous'
    else:
        return {'status': 'unique_under_trusted_analysis',
                'problem_id': next(iter(envelope.identities)),
                'analysis_contract_sha256': envelope.analysis_contract_sha256,
                'query_sha256': envelope.query_sha256,
                'universe_sha256': envelope.universe_sha256,
                'clarification_questions': [],
                'recognition_qualified': False}
    return {'status': 'abstain', 'reason': reason, 'clarification_questions': []}
