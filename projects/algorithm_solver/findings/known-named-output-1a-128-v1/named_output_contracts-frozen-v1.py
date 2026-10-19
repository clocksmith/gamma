"""Standalone candidate for complete named-output ordering declarations.

No identities, examples, or reference solutions select the contract. This module
is not imported by serving: callers explicitly bind a separate candidate query.
Only outer list order changes; data, inner order, multiplicity and existing
explicit comparisons remain intact. Unsupported wording fails closed.
"""
from dataclasses import replace
import re

_NAMES=r'(?:two integers|integers|values|substrings|paths|names|sentences|all such possible sentences)'
_DIRECT=re.compile(r'(?:Notice that you can return|You (?:may|can) return|Return) (?:the )?'+_NAMES+r' in any order',re.I)
_PASSIVE=re.compile(r'The '+_NAMES+r' (?:may|can) be returned in any order',re.I)
_NAMED_LIST=re.compile(r'Return a list that contains the names of [a-z]+(?:[- ][a-z]+)* with any order you want',re.I)
_CONDITIONAL=re.compile(r'\b(?:if|unless|provided|whenever|when|that satisfies|subject to)\b',re.I)
_ORDER_WORDS=r'(?:sorted|ascending|descending|lexicographic|lexicographical|original order|same order|increasing order|decreasing order)'
_DIRECT_CONFLICT=re.compile(r'(?:Return|You (?:must|should|need to|have to) return)\b.*\b'+_ORDER_WORDS+r'\b.*',re.I)
_REQUIRED_CONFLICT=re.compile(r'(?:The )?(?:answer|result|output|solution|'+_NAMES+r') (?:must|should|has to|needs to)\b.*\b'+_ORDER_WORDS+r'\b.*',re.I)


def declared(statement):
    requirements=re.split(r'\bExample\s*\d*\s*:',statement,maxsplit=1,flags=re.I)[0]
    sentences=[' '.join(s.split()) for s in re.split(r'[.!?\n]',requirements) if s.strip()]
    if any(_DIRECT_CONFLICT.fullmatch(s) or _REQUIRED_CONFLICT.fullmatch(s) for s in sentences):return False
    return any(not _CONDITIONAL.search(s) and any(rule.fullmatch(s) for rule in (_DIRECT,_PASSIVE,_NAMED_LIST)) for s in sentences)


def bind(problem):
    if problem.io_mode!='functional' or not declared(problem.statement):return problem
    tests=[dict(t,compare='return:unordered_outer')
           if t.get('compare','return')=='return' and type(t.get('expected')) is list else t
           for t in problem.public_tests]
    return replace(problem,public_tests=tests) if tests!=problem.public_tests else problem
