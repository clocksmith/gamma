"""Post-recognition metadata bridge; never a recognizer or a serving verdict.

Upstream owns calibrated confidence, identity and protected-boundary decisions.
The existing KnownCatalogue alone owns qualification. No source/cases/loaders are
imported, and neither language nor source availability can choose an identity.
"""
from collections.abc import Mapping
import copy

from .retrieval import KnownCatalogue


class RecognitionBridge:
    def __init__(self, catalogue: KnownCatalogue, candidate_identities: Mapping):
        """Bind lookup keys to explicit ID sequences from pinned metadata.

        This map is identity metadata, not an approval registry. Do not derive it
        by parsing titles, slugs, references or source availability. Multiple IDs
        are deliberately retained so ambiguity cannot be resolved by coverage.
        """
        if not isinstance(catalogue, KnownCatalogue):
            raise TypeError('the existing validated KnownCatalogue is required')
        if not isinstance(candidate_identities, Mapping):
            raise TypeError('candidate identity metadata must be a mapping')
        self._catalogue = catalogue
        self._identities = copy.deepcopy(dict(candidate_identities))

    def retrieve(self, match, *, boundary_check):
        """Consume answer.py's match projection after its unchanged gates.

        `match` includes decision/key/candidates/identity_check as in answer().
        `boundary_check` is a trusted upstream metadata-boundary verdict with
        `key` and a literal boolean `accepted`; it must bind this exact candidate.
        These inputs are internal gate outputs, never fields trusted from a user
        request. This adapter cannot authenticate a caller-supplied gate verdict.
        """
        def abstain(reason):
            return {'status': 'abstain', 'reason': reason,
                    'clarification_questions': []}

        if not isinstance(match, Mapping) or match.get('decision') != 'match':
            return abstain('identity_not_confident')
        key = match.get('key')
        candidates = match.get('candidates')
        if (not isinstance(key, str) or not key or
                not isinstance(candidates, (list, tuple)) or not candidates or
                not isinstance(candidates[0], Mapping) or candidates[0].get('key') != key):
            return abstain('candidate_identity_conflict')
        identity = match.get('identity_check')
        if not isinstance(identity, Mapping) or identity.get('accepted') is not True:
            return abstain('identity_not_accepted')
        if (not isinstance(boundary_check, Mapping) or
                boundary_check.get('key') != key or boundary_check.get('accepted') is not True):
            return abstain('boundary_not_accepted')
        ids = self._identities.get(key)
        if (not isinstance(ids, (list, tuple)) or not ids or
                any(not isinstance(pid, str) or not pid for pid in ids)):
            return abstain('candidate_identity_unavailable')
        unique_ids = set(ids)
        if len(unique_ids) != 1:
            return abstain('candidate_identity_ambiguous')
        value = self._catalogue.retrieve(next(iter(unique_ids)))
        value['clarification_questions'] = []
        if value['status'] == 'matched':
            value['recognition_key'] = key
            value['evidence_scope'] = (
                'upstream identity gates plus exact externally verified catalogue metadata; '
                'not query-public verification, serving approval or recognition qualification')
        return value
