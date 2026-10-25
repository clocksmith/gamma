"""Language-independent known-ID retrieval over externally verified metadata.

This is a catalogue bridge, not an informal-description recognizer. Source
materialization and execution remain in the existing isolated serving/judge lane.
"""
import copy
from .catalogue import LANGUAGES, digest, validate


class KnownCatalogue:
    def __init__(self, universe, catalogue, verified_receipts):
        universe, catalogue, receipts = copy.deepcopy((universe, catalogue, verified_receipts))
        self.summary = validate(universe, catalogue, receipts)
        self.identity = digest(catalogue)
        self._problems = {row['problem_id']: row for row in catalogue['problems']}

    def retrieve(self, problem_id):
        """Return all qualified languages for exact identity, otherwise abstain.

        Never redirect an unavailable identity to a similar approved problem.
        No language parameter influences recognition identity.
        """
        if not isinstance(problem_id, str) or not problem_id:
            return {'status': 'abstain', 'reason': 'invalid_problem_identity'}
        row = self._problems.get(problem_id)
        if row is None:
            return {'status': 'abstain', 'reason': 'unknown_problem_identity'}
        implementations = {language: copy.deepcopy(row['implementations'][language])
                           for language in LANGUAGES
                           if row['implementations'][language]['status'] == 'qualified'}
        if not implementations:
            return {'status': 'abstain', 'reason': 'no_qualified_implementation',
                    'problem_id': problem_id}
        return {'status': 'matched', 'problem_id': problem_id,
                'catalogue_sha256': self.identity, 'implementations': implementations,
                'unavailable_languages': {language: row['implementations'][language]['status']
                                          for language in LANGUAGES if language not in implementations},
                'evidence_scope': 'exact identity and externally verified metadata; no source execution or informal recognition'}

    @staticmethod
    def select_language(value, language):
        """Consumer selection does not rerun recognition or choose a sibling."""
        if language not in LANGUAGES:
            raise ValueError('unsupported consumer language')
        if value.get('status') != 'matched' or language not in value['implementations']:
            return {'status': 'abstain', 'reason': 'requested_language_unavailable'}
        return {'status': 'selected', 'problem_id': value['problem_id'],
                'language': language, 'implementation': copy.deepcopy(value['implementations'][language])}
