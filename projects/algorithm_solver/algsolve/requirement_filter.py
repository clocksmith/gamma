"""Opt-in contradiction-only recognition policy; development evidence only.

Query parsing receives text only. Candidate metadata binds by statement hash,
never by expected answer or problem ID. Unknown facts do not imply agreement.
"""
from __future__ import annotations

import copy
import hashlib
import re

from .requirements import extract

FACETS = ('ordering', 'indexing', 'layout', 'transactions', 'fee', 'cooldown',
          'output', 'updates', 'duplicates', 'changes')

# Only these existing absence concepts have an unambiguous coordinated reading.
# `no A or B` prohibits both; this is not the alternative `A or B`. An unrelated
# or outside the entire recognized span still makes the clause uncertain.
_NEGATIVE_TERM = r'(?:transaction fee|fees?|cooldown|waiting days?)'
_NEGATIVE_COORDINATION = re.compile(
    r'\bno\s+' + _NEGATIVE_TERM + r'(?:\s+(?:or|nor)\s+' + _NEGATIVE_TERM + r')+\b', re.I)


def _negative_coordinations(text):
    spans = []
    for match in _NEGATIVE_COORDINATION.finditer(text):
        terms = re.split(r'\s+(?:or|nor)\s+', re.sub(r'^no\s+', '', match.group(), flags=re.I), flags=re.I)
        facets = sorted({'fee' if 'fee' in term.lower() else 'cooldown' for term in terms})
        spans.append({'start': match.start(), 'end': match.end(), 'text': match.group(),
                      'facets': facets})
    return spans


def explicit_facts(text, *, allow_noop_option=False):
    """Extract known assertions, retaining coordinated absence and uncertainty.

    This deliberately loses coverage rather than interpreting double negation,
    alternatives, quoted requirements or hypothetical clauses as assertions.
    """
    parsed = extract(text)
    coordinated = _negative_coordinations(text)
    for span in coordinated:
        for facet in span['facets']:
            parsed['evidence'].setdefault(facet, {}).setdefault('none', []).append(
                {k: span[k] for k in ('start', 'end', 'text')})
    evidence, suppressed = {}, []
    for facet, values in parsed['evidence'].items():
        for value, spans in values.items():
            for span in spans:
                before = re.split(r'[.;!?\n]', text[:span['start']])[-1]
                sentence_start = span['start'] - len(before)
                sentence = re.split(r'[.;!?\n]', text[sentence_start:], maxsplit=1)[0]
                reason = None
                if re.search(r"\b(?:not|never|don't|do not|no)\s+(?:\w+\s+){0,3}$", before, re.I):
                    reason = 'negated_prefix'
                elif re.search(r'\b(?:if|unless|might|maybe|perhaps|possibly|assuming|suppose|could|would|either)\b', sentence, re.I):
                    reason = 'conditional_or_uncertain_clause'
                elif '"' in before or '\u201c' in before or '\u201d' in before:
                    reason = 'quoted_context'
                elif re.search(r'\b(?:or|nor)\b', sentence, re.I) and facet != 'output':
                    ors = [sentence_start + m.start() for m in re.finditer(r'\b(?:or|nor)\b', sentence, re.I)]
                    negative_assertion = value == 'none' and any(
                        facet in group['facets'] and group['start'] <= span['start'] < group['end']
                        and all(group['start'] <= position < group['end'] for position in ors)
                        for group in coordinated)
                    # A trailing zero-action option does not change an explicit
                    # transaction upper bound. This is opt-in and deliberately
                    # excludes arbitrary alternatives, conditions and quotations.
                    noop = re.search(r'\bor\s+do\s+nothing\s*$', sentence, re.I)
                    noop_option = (allow_noop_option and facet == 'transactions'
                                   and value in ('one', 'two', 'unlimited') and noop
                                   and span['end'] <= sentence_start + noop.start()
                                   and all(sentence_start + noop.start() <= p for p in ors))
                    if not negative_assertion and not noop_option:
                        reason = 'alternative_clause'
                if reason:
                    suppressed.append(dict(span, facet=facet, value=value, reason=reason))
                else:
                    evidence.setdefault(facet, {}).setdefault(value, []).append(span)
    facts = {f: next(iter(vs)) for f, vs in evidence.items() if len(vs) == 1}
    conflicts = {f: vs for f, vs in evidence.items() if len(vs) > 1}
    return {'facts': facts, 'conflicts': conflicts, 'evidence': evidence,
            'suppressed': suppressed, 'scope': 'conservative explicit development grammar; unknown stays unknown'}


def contradicts(facet, requested, source):
    # A source allowing arbitrary ordering also permits sorted input. Never
    # reject that source merely because the request supplies a narrower input.
    if facet == 'ordering' and requested == 'sorted' and source == 'arbitrary':
        return False
    return requested != source


class RequirementFilter:
    def __init__(self, profiles, *, allow_noop_option=False):
        self.allow_noop_option = allow_noop_option
        self.profiles = {}
        for profile in profiles:
            h = profile['statement_sha256']
            facts = {f: v for f, v in profile['facts'].items() if f in FACETS}
            if h in self.profiles and self.profiles[h] != facts:
                raise ValueError('Conflicting source contracts for one statement hash')
            self.profiles[h] = facts

    def apply(self, text, candidates, lookup):
        parsed = explicit_facts(text, allow_noop_option=self.allow_noop_option)
        kept, audit = [], []
        for candidate in candidates:
            entry = lookup.entries[lookup.by_key[candidate['key']]]
            h = hashlib.sha256(entry.statement.encode()).hexdigest()
            facts = self.profiles.get(h)
            contradictions = []
            if not parsed['conflicts'] and facts is not None:
                for facet, value in parsed['facts'].items():
                    if facet in FACETS and facet in facts and contradicts(facet, value, facts[facet]):
                        contradictions.append({'facet': facet, 'query': value, 'source': facts[facet],
                                               'query_evidence': parsed['evidence'][facet][value]})
            excluded = bool(contradictions)
            audit.append({'candidate': copy.deepcopy(candidate), 'statement_sha256': h,
                          'source_facts': facts, 'profile_bound': facts is not None,
                          'excluded': excluded, 'contradictions': contradictions,
                          'reason': 'explicit_contract_contradiction' if excluded else
                          ('query_conflicts_no_selection' if parsed['conflicts'] else
                           'compatible_or_unknown' if facts is not None else 'unprofiled_or_stale_unknown')})
            if not excluded:
                kept.append(copy.deepcopy(candidate))
        reason = ('conflicting_requirements' if parsed['conflicts'] else
                  'all_candidates_contradict_requirements' if candidates and not kept else None)
        return ([] if parsed['conflicts'] else kept), {
            'query': parsed, 'pre_filter': copy.deepcopy(candidates),
            'post_filter': [] if parsed['conflicts'] else copy.deepcopy(kept),
            'audit': audit, 'reason': reason,
            'scope': 'contradiction exclusion only; not equivalence or qualification'}


class PolicyLookup:
    """Apply after the existing interface filter without altering answer.py.

    answer() repeats the deterministic interface filter on the returned subset.
    Its cost is measured; the original interface exclusions remain in this audit.
    """
    def __init__(self, lookup, policy, examples):
        self.lookup, self.policy, self.examples = lookup, policy, examples
        self.trace = None

    def __getattr__(self, name):
        return getattr(self.lookup, name)

    def scored_candidates(self, text, vector):
        from .interface_compatibility import filter_candidates
        raw = self.lookup.scored_candidates(text, vector)
        compatible, rejected = filter_candidates(raw, self.lookup, self.examples)
        result, trace = self.policy.apply(text, compatible, self.lookup)
        self.trace = dict(trace, raw_retrieval=copy.deepcopy(raw), interface_rejections=rejected)
        return result


def answer_with_policy(context, query, approved, policy):
    from .answer import answer
    local = copy.copy(context)
    adapter = PolicyLookup(context.lookup, policy, query.public_tests)
    local.lookup = adapter
    result = answer(local, query, approved_library=approved)
    if adapter.trace is not None:
        result['requirement_filter'] = adapter.trace
        if adapter.trace['reason']:
            if result['decision'] != 'abstain':
                raise AssertionError('Conflicting or empty requirements must abstain')
            result['route_reason'] = result.get('reason')
            result['reason'] = adapter.trace['reason']
    return result
