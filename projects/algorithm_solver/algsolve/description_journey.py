"""Description -> requirements/clarification -> checked stored code.

Three bounded routes share embedding retrieval and query-owned public checks.
Curated profiles cover development families only; unknown semantics abstain.
No independent tests, target identities or generated source enter this object.
"""
from __future__ import annotations

import copy
from dataclasses import replace
import hashlib
import time

from .answer import check_stored
from .clarify import ClarificationSession
from .lookup import decide
from .public_examples import recover
from .requirements import extract

ROUTES = ('embedding_only', 'requirement_selection', 'selection_clarification')


class DescriptionJourney:
    def __init__(self, context, query, catalog, thresholds, *, route):
        if route not in ROUTES:
            raise ValueError('Unknown description route')
        self.context = context
        self.query = recover(replace(query, hidden_tests_path='', reference_solutions=[], import_notes={}))
        self.route = route
        self.thresholds = copy.deepcopy(thresholds)
        self.catalog = copy.deepcopy(catalog)
        self.profiles = {p['key']:p for p in self.catalog['profiles']}
        self.machine_seconds = 0.
        self.confirmations = 0
        self.session = None
        self.result = None
        self.selection = None
        self.candidates = []
        self.requirements = None

    def _finish(self, reason, key=None, code=None, verdict=None):
        entry = self.context.entries[self.context.lookup.by_key[key]] if key else None
        self.result = {'decision':'answered' if code else 'abstain', 'reason':reason,
                       'key':key, 'code':code, 'route':self.route,
                       'example_passed':bool(verdict and verdict.passed),
                       'public_verdict':verdict.to_dict() if verdict else None,
                       'independent_tests_passed':None,
                       'source':{'key':key,'license':entry.license,'attribution':entry.attribution} if entry else None,
                       'selection_basis':self.selection, 'candidates':copy.deepcopy(self.candidates),
                       'requirements':self.requirements,
                       'questions':self.session.questions if self.session else 0,
                       'confirmations':self.confirmations}
        return self.result

    def _check(self, key):
        if not self.query.public_tests:
            return self._finish('query_has_no_public_examples',key)
        entry = self.context.entries[self.context.lookup.by_key[key]]
        remaining = self.context.budget.route_wall_seconds - self.machine_seconds - (time.perf_counter()-self._operation_start)
        if remaining <= 0:
            return self._finish('budget_exhausted',key)
        code, verdict = check_stored(self.query,entry,min(remaining,self.context.budget.judge_wall_seconds))
        return self._finish('public_examples_passed' if code else 'public_check_failed',key,code,verdict)

    def _advance(self, step):
        if step['decision'] == 'match':
            self.selection = 'user_confirmed_statement'
            return self._check(step['key'])
        if step['decision'] == 'abstain':
            return self._finish(step['reason'])
        if step['decision'] == 'confirm':
            entry = self.context.entries[self.context.lookup.by_key[step['candidate']['key']]]
            actual = hashlib.sha256(entry.statement.encode()).hexdigest()
            if actual != step['candidate']['statement_sha256']:
                return self._finish('profile_statement_changed')
            step = copy.deepcopy(step)
            step['statement'] = entry.statement
            step['attribution'] = entry.attribution
            step['license'] = entry.license
        return step

    def start(self):
        if self.candidates or self.result is not None or self.session:
            raise ValueError('Journey already started')
        self._operation_start = time.perf_counter()
        try:
            text = self.query.query_text()
            vector = self.context.embedder.encode([text],query=True)[0]
            scored = self.context.lookup.scored_candidates(text,vector)
            # Pure embedding control: no method/number/phrase feature bonuses.
            self.candidates = sorted([dict(c,score=c['cosine']) for c in scored],key=lambda c:(-c['score'],c['key']))
            if not self.candidates:
                return self._finish('empty_index')
            if self.route == 'embedding_only':
                match = decide(self.candidates,self.thresholds['embedding_only'])
                if match.decision != 'match':
                    return self._finish('embedding_abstained')
                self.selection = 'embedding_threshold'
                return self._check(match.key)
            self.requirements = extract(self.query.statement)
            if self.requirements['conflicts']:
                return self._finish('conflicting_requirements')
            self.session = ClarificationSession(self.query.statement,self.candidates,self.catalog,
                                                facts=self.requirements['facts'])
            if self.route == 'selection_clarification':
                return self._advance(self.session.next_step())
            # Automatic selection must have explicit support for every declared
            # profile fact, not merely a high similarity or missing contradiction.
            facts = self.requirements['facts']
            supported = [c for c in self.candidates if c['key'] in self.session.active and
                         all(facts.get(f)==v for f,v in self.profiles[c['key']]['facts'].items())]
            if not supported:
                return self._finish('requirements_incomplete_or_unprofiled')
            match = decide(supported,self.thresholds['requirement_selection'])
            if match.decision != 'match':
                return self._finish('requirement_score_abstained')
            self.selection = 'explicit_profile_facts_and_development_threshold'
            return self._check(match.key)
        finally:
            self.machine_seconds += time.perf_counter()-self._operation_start
            if self.result is not None:
                self.result['seconds'] = self.machine_seconds

    def reply(self, question_id, value, *, reviewed_statement_sha256=None):
        if self.result is not None or self.session is None:
            raise ValueError('No pending journey question')
        self._operation_start = time.perf_counter()
        try:
            was_confirmation = self.session.pending and self.session.pending['decision']=='confirm'
            step = self.session.answer(question_id,value,reviewed_statement_sha256=reviewed_statement_sha256)
            self.confirmations += int(bool(was_confirmation))
            return self._advance(step)
        finally:
            self.machine_seconds += time.perf_counter()-self._operation_start
            if self.result is not None:
                self.result['seconds'] = self.machine_seconds

    def cancel(self):
        if self.result is not None:
            return self.result
        if self.session:
            self.session.cancel()
        result = self._finish('cancelled')
        result['seconds'] = self.machine_seconds
        return result
