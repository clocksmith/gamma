"""Opt-in answer-changing facet gate for one-input stored recognition (development).

Every indexed source carries a contract: its family, its completeness review,
the facts that separate it from siblings and from material alternative
readings, and the facets a request must settle before a non-exact stored answer
returns. An unreviewed source abstains: an empty or partial facet list is not
proof of identity. A required facet is settled by explicit, certain query
evidence. A contract document may additionally declare absence defaults for
add-on features (used only by labelled ablations); trade count, duplicate
policy, output and the other no-default facets can never default. Source facts,
public examples and sibling absence never fill an omission. The gate only
rejects: the selected source is never replaced.

The grammar is a conservative phrase grammar, not a language model. Evidence is
uncertain when a hedge or conditional precedes it in its clause, when the
sentence opens with a conditional, when it is quoted, when an absence phrase is
itself negated (`it is not true that there are no fees`), or when `or`/`nor`
within two words of it offers an alternative (a recognized `no A or B` absence
list and a trailing fallback such as `or zero` are not alternatives).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

# (facet, value, pattern, encodes_negation). Patterns that themselves contain a
# negation are exempt from the negated-prefix rule.
RULES = [
    # stock
    ('transactions', 'one', r"\b(?:buy (?:it |the stock |a share |one share )?once|(?:only |just |exactly )?(?:one|a single|1) (?:completed |single )?(?:trade|transaction|purchase|round trip)s?\b|at most one (?:trade|transaction)|one buy and one sell|a single buy and (?:a single )?sell)", False),
    ('transactions', 'two', r"\b(?:at most (?:two|2) (?:completed )?(?:trades|transactions)|up to (?:two|2) (?:completed )?(?:trades|transactions)|(?:two|2) (?:separate |completed |non-?overlapping )?(?:trades|transactions))\b", False),
    ('transactions', 'k', r"\b(?:at most k (?:completed )?(?:trades|transactions)|up to k (?:trades|transactions)|k (?:completed )?(?:trades|transactions))\b", False),
    ('transactions', 'unlimited', r"\b(?:repeatedly buy|buy and sell (?:as many times|repeatedly|multiple times|any number of times)|as many (?:trades|transactions|times) as (?:i|you|we) (?:want|like|wish)|as often as (?:i|you|we) (?:want|like|wish)|any number of (?:stock )?(?:trades|transactions|times)|unlimited (?:number of )?(?:trades|transactions)|no limit on (?:the number of )?(?:trades|transactions)|multiple (?:trades|transactions))\b", False),
    ('fee', 'none', r"\b(?:no (?:transaction |trading )?(?:fees?|commissions?)|fee[- ]free|without (?:any )?(?:fees?|commissions?)|free of (?:charge|fees))\b", True),
    ('fee', 'per_trade', r"\b(?:transaction fee|(?:a )?fee (?:of|per|for each|on each)|costs? (?:a )?commission|commission (?:per|on each|for each|exactly once)|pay (?:a|the) fee|charged (?:a fee )?(?:once )?(?:per|for each) (?:completed )?(?:trade|transaction))\b", False),
    ('cooldown', 'none', r"\b(?:no (?:cooldown|cool-down|waiting (?:days?|period))|without (?:a |any )?(?:cooldown|cool-down|waiting (?:day|period)))\b", True),
    ('cooldown', 'one_day', r"\b(?:cooldown|cool-down|sit out the next day|wait (?:one|a|1) (?:full )?day|wait the next day|skip the (?:next|following) day|rest (?:for )?(?:one|a) day)\b", False),
    # houses and subarrays
    ('layout', 'circle', r"\b(?:circle|circular|ring|wraps? around|closed block|last (?:house|element|number|one) (?:touches|is adjacent to|neighbors|is next to) the first|first and last (?:houses? |elements? )?are (?:also )?(?:adjacent|neighbou?rs))\b", False),
    ('layout', 'line', r"\b(?:straight (?:street|line|row)|in a (?:row|line|straight line)|row of houses|first and last (?:houses? |elements? )?(?:are not|aren't) (?:adjacent|neighbou?rs)|not (?:circular|a circle|cyclic)|(?:doesn't|does not) wrap(?: around)?)\b", True),
    ('layout', 'tree', r"\bbinary tree\b", False),
    ('deletion', 'one', r"\b(?:(?:delete|remove|drop|skip) (?:at most |up to )?one (?:element|number|value|item|entry)|one deletion|at most one deletion)\b", False),
    # islands
    ('output', 'count', r"\b(?:how many (?:separate |closed |enclosed |isolated )?(?:islands|land masses|landmasses|land regions|groups of land)|number of (?:separate |closed |enclosed |isolated )?(?:islands|land masses)|count (?:the |all )?(?:separate |closed |enclosed |isolated )?(?:islands|land masses))\b", False),
    ('output', 'area', r"\b(?:(?:largest|biggest|maximum|max) (?:island|land mass|patch|component|connected (?:patch|component|region|area|group))|area of the (?:largest|biggest) island|max(?:imum)? (?:island )?area|largest possible island)\b", False),
    ('output', 'cells', r"\b(?:(?:number of|how many|count (?:the )?) ?(?:land )?cells (?:from which|for which|that (?:cannot|can't|can never)|which (?:cannot|can't))|land cells (?:that|which|from which) (?:cannot|can't|never))", False),
    ('output', 'distinct_shapes', r"\b(?:distinct (?:islands|shapes)|different (?:island )?shapes|unique (?:island )?shapes)\b", False),
    ('output', 'bridge', r"\b(?:shortest bridge|(?:connect|join) the two islands|minimum (?:number of )?(?:flips|cells|zeros) to (?:connect|join))\b", False),
    ('output', 'bordered_square', r"\b(?:bordered square|square (?:sub-?grid )?(?:with|whose) (?:all )?(?:1s|ones) (?:on|along) (?:its|the) border|border made (?:entirely )?of (?:1s|ones))\b", False),
    ('border', 'interior', r"\b(?:closed islands?|surrounded by water on all (?:four )?sides|(?:does not|doesn't|do not|don't|never|cannot|can't) (?:touch|reach|connect to) the (?:border|edge|boundary)|(?:not|never) (?:touching|reaching|connected to) the (?:border|edge|boundary)|walk off the (?:border|edge) of the grid)\b", True),
    ('transform', 'rotation_reflection', r"\b(?:rotations? (?:or|and|and/or) reflections?|reflections? (?:or|and|and/or) rotations?|rotat(?:e|ed|ion|ions)|reflect(?:ed|ion|ions)?|mirror(?:ed|ing)?)\b", False),
    ('transform', 'translation', r"\b(?:translat(?:e|ed|ion|ions)|same shape (?:after|by) (?:moving|shifting)|without rotat(?:ing|ion)(?: or reflect(?:ing|ion))?)\b", False),
    ('changes', 'one_flip', r"\b(?:change at most one (?:0|zero) to (?:a )?(?:1|one)|flip (?:at most )?one (?:0|zero|water cell)|turn (?:at most )?one (?:0|zero|water cell) into land|convert (?:at most )?one (?:0|zero))\b", False),
    ('changes', 'none', r"\b(?:without (?:adding|changing) (?:any )?(?:land|cells)|no cell changes|do not (?:add|change) (?:any )?(?:land|cells))\b", True),
    # courses
    ('output', 'possible', r"\b(?:true or false|whether (?:it is possible|(?:all|every) (?:the )?courses? can be (?:completed|finished|taken))|can (?:i|you|we) (?:finish|complete|take) (?:all|every)(?: of)?(?: the)? courses?|possible to (?:finish|complete|take) (?:all|every))\b", False),
    ('output', 'order', r"\b(?:return (?:any |a |one )?(?:valid )?(?:ordering|order of (?:the |all )?courses|topological order|schedule|course order)|order in which to take|list (?:of )?(?:the )?courses in (?:a |an )?(?:valid )?order)\b", False),
    # pairs and sorted search
    ('output', 'positions', r"\b(?:(?:the |their )?(?:two|both) (?:zero-based |one-based |0-based |1-based )?(?:positions|indices|indexes)|return (?:the |their )?(?:two )?(?:positions|indices|indexes) of|indices of the two)\b", False),
    ('output', 'insert_position', r"\b(?:(?:index|position) where (?:it|the target|target) would be inserted|insert(?:ion)? (?:index|position|point)|where (?:it|the target|target) (?:would|should) (?:go|be inserted))\b", False),
    ('output', 'range', r"\b(?:first and last (?:positions?|indices|indexes|occurrences?)|starting and ending (?:positions?|indices)|leftmost and rightmost)\b", False),
    ('output', 'target_indices', r"\b(?:ind(?:ices|exes) (?:of|where) (?:the )?target (?:after|once|when) (?:sorting|sorted|the (?:list|array) is sorted)|after sorting,? (?:return|list|give) (?:all |the )?(?:indices|positions))\b", False),
    ('ordering', 'sorted', r"\b(?:sorted (?:in )?(?:ascending|non-?decreasing|increasing)(?: order)?|(?:is|are|already|comes) sorted|sorted (?:list|array|input|numbers|values))\b", False),
    ('ordering', 'arbitrary', r"\b(?:unsorted|not (?:necessarily )?sorted|in arbitrary order|no sorted[- ]order guarantee)\b", True),
    ('indexing', 'zero', r"\b(?:zero[- ]based|0[- ]based|zero[- ]indexed|0[- ]indexed|counting (?:positions )?from zero)\b", False),
    ('indexing', 'one', r"\b(?:one[- ]based|1[- ]based|one[- ]indexed|1[- ]indexed|counting (?:positions )?from one)\b", False),
    # rank
    ('output', 'kth', r"\b(?:k-?th|rank-?th|\d+(?:st|nd|rd|th)) (?:largest|biggest|highest|greatest)\b", False),
    ('output', 'ranks', r"\b(?:replace each (?:element|value|number|entry) (?:with|by) its rank|rank of (?:each|every) (?:element|value|number))\b", False),
    ('duplicates', 'occurrences', r"\b(?:counting duplicates?(?: occurrences)? separately|duplicates? (?:are )?(?:count(?:ed)?|treated) (?:separately|individually|as separate)|(?:repeated|duplicate) (?:values?|numbers?|occurrences) (?:each )?(?:count|counted|take their own)|including duplicates|not (?:necessarily )?(?:the )?(?:kth )?distinct)\b", True),
    ('duplicates', 'distinct', r"\b(?:distinct values?|distinct numbers?|distinct elements?|each distinct value once|ignor(?:e|ing) duplicates|duplicates? (?:are )?(?:count(?:ed)?|treated) once|unique values?)\b", False),
    ('duplicates', 'shared_rank', r"\b(?:equal (?:elements|values|numbers) (?:get|have|share|receive) the same rank|same rank for equal|ties share (?:a|the same) rank)\b", False),
    ('updates', 'stream', r"\b(?:stream(?:ing)?|after each (?:insertion|addition|new (?:value|number))|as (?:numbers|values) arrive|one at a time as)\b", False),
    # frequency
    ('output', 'frequent', r"\b(?:k most frequent|most frequent k|top[- ]k (?:most )?frequent|(?:which|the) k (?:distinct )?(?:values|numbers|elements|integers) (?:that )?(?:occur|appear) (?:the )?most (?:often|frequently)|k (?:values|elements|numbers) with the highest frequenc(?:y|ies))\b", False),
    ('output', 'remaining_unique', r"\b(?:(?:least|fewest|minimum|smallest) number of (?:unique|distinct) (?:integers|values|numbers)|fewest (?:unique|distinct) (?:integers|values|numbers))\b", False),
    # windows with a target
    ('output', 'shortest_window', r"\b(?:(?:shortest|smallest|minimum|minimal) (?:length |size )?(?:consecutive |contiguous )?(?:slice|subarray|sub-array|window|run|segment|stretch)|minimum (?:size|length) (?:of )?(?:a )?(?:subarray|window|slice))\b", False),
    ('output', 'count_nonoverlapping', r"\b(?:(?:maximum|largest|greatest) number of non-?overlapping|most non-?overlapping)\b", False),
    ('output', 'two_windows', r"\btwo non-?overlapping (?:subarrays|sub-arrays|slices|windows|segments)\b", False),
    ('output', 'longest_subsequence', r"\b(?:longest subsequence|(?:maximum|largest) (?:length|size) (?:of )?(?:a |any )?subsequence)\b", False),
    ('repetition', 'infinite', r"\b(?:infinite(?:ly)?|repeat(?:s|ed)? (?:forever|endlessly|infinitely)|appended to itself (?:forever|infinitely|repeatedly)|concatenat\w+ (?:infinitely|forever|endlessly))\b", False),
    ('repetition', 'none', r"\b(?:not repeated|(?:doesn't|does not|never) repeat|(?:array|list) (?:is )?(?:used |taken )?as given|no repetition)\b", True),
    # facets found by the material-alternative review (never defaulted)
    ('holding', 'one_share', r"\b(?:(?:hold|holding|own|owning|keep) (?:at most |only |just )?(?:one|a single|1) share|one share at a time|at most one share|(?:must|have to|need to) sell (?:it |the stock |the share )?before (?:buying|you buy|i buy)|sell before (?:you |i )?buy(?:ing)? again|(?:cannot|can't) hold more than one|no more than one share)\b", True),
    ('adjacency', 'no_adjacent', r"\b(?:(?:never|not|cannot|can't|don't|do not|no|without) (?:\w+ ){0,3}(?:two )?(?:adjacent|neighbou?ring|neighbou?rs|consecutive|next-door)|non-?adjacent)\b", True),
    ('connectivity', 'four', r"\b(?:(?:4|four)[- ](?:directional(?:ly)?|directions?|connected|neighbou?rs?|neighbou?rhood)|up,? down,? left,? (?:and|or) right|horizontally (?:and|or) vertically|vertically (?:and|or) horizontally|(?:not|never|no) diagonal(?:ly|s)?|shared edges|shares? an edge|edge[- ]adjacent)\b", True),
    ('connectivity', 'eight', r"\b(?:(?:8|eight)[- ](?:directional(?:ly)?|directions?|connected|neighbou?rs?)|(?:including|also|and) diagonal(?:ly|s)?|diagonals? (?:also )?count)\b", False),
    ('solutions', 'exactly_one', r"\b(?:exactly one (?:solution|pair|answer|valid pair)|(?:has|have|is) exactly one|(?:a |the )?unique (?:solution|pair)|only one (?:valid )?(?:solution|pair))\b", False),
    ('reuse', 'distinct_positions', r"\b(?:(?:at |two )?different (?:positions|indices|indexes|elements)|(?:same|one) (?:position|element|index) (?:can't|cannot|may not|must not|can not) be used twice|not use the same (?:element|position|index) twice|two distinct (?:positions|indices|indexes)|distinct (?:positions|indices|indexes))\b", True),
    ('positivity', 'positive', r"\b(?:(?:all|every|each) (?:of the )?(?:numbers|values|elements|integers|entries)(?: in [\w ]{1,20}?)? (?:are|is) (?:strictly )?positive|positive (?:integers|numbers|values|entries))\b", False),
    ('fallback', 'zero', r"\b(?:(?:return |give |output )?(?:0|zero) if (?:none|no such|there is no|there's no|nothing|no (?:subarray|slice|window))|or (?:0|zero) if)\b", False),
    ('nonempty', 'yes', r"\b(?:non-?empty|at least one (?:element|number|value|item|entry)|(?:cannot|can't) be empty|must (?:contain|include|pick) at least one)\b", True),
    ('output', 'max_sum', r"\b(?:(?:greatest|largest|maximum|biggest|highest) (?:possible )?(?:total )?sum|max(?:imum)? subarray sum)\b", False),
    ('ties', 'unique_answer', r"\b(?:(?:the )?answer (?:set )?is (?:guaranteed (?:to be )?)?unique|guaranteed (?:to be )?unique|unique answer|no ties)\b", False),
    ('answer_order', 'any', r"\b(?:(?:in )?any (?:output )?order|order (?:does not|doesn't) matter|any output order|in either order)\b", False),
    ('rank_base', 'one', r"\b(?:ranks? (?:start|starts|begin|begins) (?:at|from) (?:1|one)|(?:starting|start) (?:at|from) (?:1|one)|smallest (?:rank|value|element) (?:gets|is|has) (?:rank )?(?:1|one))\b", False),
    ('prereq_direction', 'second_first', r"(?:\[\s*a\s*,\s*b\s*\] (?:means|says|indicates) (?:(?:that|do|you must|i must|we must) )?(?:take |complete |finish |do )?b (?:\w+ ){0,3}before a|\bb (?:must|has to|needs to) be (?:taken|completed|finished|done) before a|\bto take a,? (?:you|i|we) must (?:first )?take b)\b", False),
    ('border', 'any', r"\b(?:outside (?:the (?:map|grid|matrix) )?is (?:all )?water|(?:all )?(?:four )?edges of the (?:grid|map) are (?:all )?surrounded by water|(?:assume|treat) (?:everything |the area )?outside (?:the (?:grid|map) )?(?:as|is) water|islands? touching the (?:edge|border) (?:still )?counts?)\b", False),
    ('updates', 'batch', r"\b(?:(?:one|a|this|the given|the) (?:fixed |static )?(?:array|list)|in (?:items|nums|this array|this list))\b", False),
    ('relation', 'at_least', r"(?:\b(?:at least|reaches or exceeds|greater than or equal to|no less than|meets or exceeds)\b|>=)", True),
    ('relation', 'exactly', r"\b(?:(?:sums?|adds? up|add up) (?:exactly )?to (?:the )?target|exactly (?:equal to |equals )?(?:the )?target|equals? (?:the )?target|equal to (?:the )?target)\b", False),
    ('deletion', 'none', r"\b(?:no deletions?|without (?:deleting|removing) (?:any|anything)|(?:cannot|can't|may not) (?:delete|remove) (?:any|anything))\b", True),
]
_COMPILED = [(f, v, re.compile(p, re.I), neg) for f, v, p, neg in RULES]
NEVER_DEFAULT = {'transactions', 'duplicates', 'output', 'holding', 'adjacency', 'connectivity', 'solutions', 'reuse',
                 'positivity', 'fallback', 'nonempty', 'ties', 'answer_order', 'rank_base', 'prereq_direction', 'relation'}
# An add-on feature is absent only if the request never mentions it. A mention that the grammar cannot read
# (for example `if there is a fee, it is per trade`) blocks the default instead of being ignored.
MENTIONS = {k: re.compile(p, re.I) for k, p in {
    'fee': r'\b(?:fees?|commissions?|charge[sd]?|costs? per)\b',
    'cooldown': r'\b(?:cooldowns?|cool-downs?|waiting|wait (?:a|one|the|for)|sit out)\b',
    'layout': r'\b(?:circle|circular|ring|wraps?|cyclic|around)\b',
    'deletion': r'\b(?:delet\w*|remov\w*|drop\w*)',
    'repetition': r'\b(?:infinit\w*|repeat\w*|concatenat\w*|cycl\w*)',
    'border': r"\b(?:borders?|boundar\w*|closed|enclaves?|enclosed|surrounded|(?:grid|map|matrix)'?s? edges?|edges? of the (?:grid|map|matrix)|off the edge)\b",
    'transform': r'\b(?:rotat\w*|reflect\w*|mirror\w*|translat\w*|congruent)',
    'changes': r'\b(?:flip\w*|chang\w*|convert\w*|turn\w* (?:one|a|at most))',
    'updates': r'\b(?:stream\w*|insert\w*|arriv\w*|online)\b',
    'ordering': r'\b(?:sorted|unsorted|ascending|descending|non-?decreasing|increasing order|decreasing order)\b',
    'indexing': r'\b(?:(?:zero|one|0|1)[- ](?:based|indexed)|counting (?:positions )?from|start(?:s|ing)? (?:at|from) (?:zero|one|0|1))\b',
}.items()}
FACETS = tuple(dict.fromkeys(f for f, *_ in RULES))
_NEG_TERM = r'(?:transaction fees?|trading fees?|fees?|commissions?|cooldowns?|cool-downs?|waiting days?|waiting periods?)'
_NEG_LIST = re.compile(r'\b(?:no|without(?: any)?)\s+' + _NEG_TERM + r'(?:\s*(?:,|or|nor|and)\s+(?:any\s+)?' + _NEG_TERM + r')+\b', re.I)
_NEGATION = re.compile(r"\b(?:not|never|don't|do not|doesn't|does not|no|without|cannot|can't|isn't|aren't|won't)\s+(?:\w+\s+){0,3}$", re.I)
# Permission words (may, can, could) are not hedges in problem statements.
_HEDGE = re.compile(r'(?<!same )(?<!equal )(?<!identical )(?<!equivalent )\b(?:if|unless|maybe|might|perhaps|possibly|assuming|suppose|supposing|either|optionally)\b', re.I)  # `the same if` defines, it does not hedge
_OPENING = re.compile(r'^\s*(?:if|unless|suppose|supposing|assuming|when|whenever)\b', re.I)
_OR = re.compile(r'\b(?:or|nor)\b', re.I)
# A negation earlier in the sentence than an absence phrase (`it is not true that there are no fees`).
# Only a negation that scopes over the phrase counts: `not true that`, `false that`, or `not` right before it.
_DOUBLE = re.compile(r"(?:\b(?:not|never)\s+$|\b(?:not|never|isn't) (?:true|the case)(?: that)?\b|\b(?:false|untrue|wrong) (?:that|to say)\b|\b(?:doesn't|does not|don't|do not) (?:mean|say|claim)(?: that)?\b)", re.I)
_FALLBACK = re.compile(r'\b(?:or|nor)\s+(?:else\s+)?(?:do nothing|zero|0|-1|minus one|an? empty|empty|none|null|nothing|false|return)\b', re.I)
_SENTENCE = re.compile(r'[.;!?\n]+')
_SEGMENT = re.compile(r',|\bbut\b|\bwhile\b|\bhowever\b|\bthough\b|:|\(|\)|—|–| - ', re.I)


def _spans(pattern, text):
    return [(m.start(), m.end()) for m in pattern.finditer(text)]


def parse(text):
    """{facts, conflicts, uncertain, evidence}: unknown stays unknown."""
    neg_lists = []
    for m in _NEG_LIST.finditer(text):
        terms = m.group().lower()
        facets = [f for f, key in (('cooldown', r'cool|wait'), ('fee', r'fee|commission')) if re.search(key, terms)]
        neg_lists.append((m.start(), m.end(), facets))
    certain, uncertain = {}, {}
    hits = []
    for facet, value, pattern, encodes_negation in _COMPILED:
        for m in pattern.finditer(text):
            hits.append((m.start(), m.end(), facet, value, encodes_negation))
    for s, e, facets in neg_lists:
        for facet in facets:
            hits.append((s, e, facet, 'none', True))
    for s, e, facet, value, encodes_negation in hits:
        sent_start = max([0] + [m.end() for m in _SENTENCE.finditer(text, 0, s)])
        sent_end = (_SENTENCE.search(text, e) or re.search(r'$', text)).start()
        bounds = [sent_start] + [sent_start + b for _, b in _spans(_SEGMENT, text[sent_start:sent_end])] + [sent_end]
        seg_start = max(b for b in bounds if b <= s)
        seg_end = min([b for b in bounds if b >= e] + [sent_end])
        before = text[seg_start:s]
        in_neg_list = any(a <= s and e <= b for a, b, _ in neg_lists)
        if not encodes_negation and (in_neg_list or _NEGATION.search(before)):
            continue  # negated mention of a positive value: not evidence for it
        reason = None
        if (encodes_negation or in_neg_list) and _DOUBLE.search(before):
            reason = 'double_negation'
        elif _HEDGE.search(before) or _OPENING.match(text[sent_start:s]):
            reason = 'conditional_or_hedged'
        elif text[:s].count('"') % 2 or text[:s].count('“') > text[:s].count('”'):
            reason = 'quoted'
        else:
            segment = text[seg_start:seg_end]
            fallbacks = _spans(_FALLBACK, segment)
            for a, b in _spans(_OR, segment):
                p, q = seg_start + a, seg_start + b
                if s <= p < e or any(x <= p < y for x, y, _ in neg_lists):
                    continue  # `or` inside the matched phrase or inside a recognized absence list
                if any(fa == a for fa, _ in fallbacks) and p >= e:
                    continue  # trailing fallback answer, not an alternative requirement
                gap = text[e:p] if p >= e else text[q:s]
                if len(gap.split()) > 2:
                    continue  # an `or` that coordinates other words of the clause, not this phrase
                reason = 'alternative'
                break
        span = {'start': s, 'end': e, 'text': text[s:e]}
        (uncertain if reason else certain).setdefault(facet, {}).setdefault(value, []).append(dict(span, reason=reason) if reason else span)
    facts = {f: next(iter(vs)) for f, vs in certain.items() if len(vs) == 1}
    conflicts = {f: sorted(vs) for f, vs in certain.items() if len(vs) > 1}
    unsure = sorted(f for f, vs in uncertain.items() if f not in facts or set(vs) - {facts[f]})
    return {'facts': facts, 'conflicts': conflicts, 'uncertain': unsure, 'certain_evidence': certain,
            'uncertain_evidence': uncertain, 'scope': 'conservative phrase grammar; unknown stays unknown'}


class FacetGate:
    def __init__(self, document):
        if document.get('schema_version') != 1:
            raise ValueError('Unsupported facet-gate schema')
        self.defaults = dict(document['absence_defaults'])
        self.compatible = {tuple(x) for x in document.get('compatible', [])}
        if set(self.defaults) - set(MENTIONS) or NEVER_DEFAULT & set(self.defaults):
            raise ValueError('Defaults are allowed only for declared add-on features')
        self.contracts = {}
        for c in document['contracts']:
            h, facts, required = c['statement_sha256'], c['facts'], c['required_facets']
            if (not re.fullmatch(r'[0-9a-f]{64}', h) or not isinstance(facts, dict) or not isinstance(required, list)
                    or len(set(required)) != len(required) or not set(required) <= set(facts) <= set(FACETS)
                    or any(not isinstance(v, str) or not v for v in facts.values()) or h in self.contracts):
                raise ValueError(f"Invalid or duplicate facet contract: {c.get('source_key')}")
            if c.get('completeness') not in ('reviewed', 'unreviewed'):
                raise ValueError(f"Contract completeness must be reviewed or unreviewed: {c['source_key']}")
            self.contracts[h] = {'source_key': c['source_key'], 'family': c['family'], 'facts': dict(facts),
                                 'required_facets': sorted(required), 'completeness': c['completeness']}

    def agrees(self, facet, requested, source):
        return requested == source or (facet, requested, source) in self.compatible

    def check(self, text, entry):
        h = hashlib.sha256(entry.statement.encode()).hexdigest()
        contract = self.contracts.get(h)
        parsed = parse(text)
        result = {'accepted': False, 'statement_sha256': h, 'contract': copy.deepcopy(contract), 'query': parsed,
                  'scope': 'declared answer-changing facets only; not semantic equivalence'}
        if contract is None:
            return dict(result, reason='facet_gate_unbound_source')
        if contract['completeness'] != 'reviewed':
            return dict(result, reason='facet_gate_unreviewed_source')
        facts = contract['facts']
        conflicts = sorted(set(parsed['conflicts']) & set(facts))
        contradictions = [{'facet': f, 'query': v, 'source': facts[f]} for f, v in parsed['facts'].items()
                          if f in facts and not self.agrees(f, v, facts[f])]
        uncertain = sorted(set(parsed['uncertain']) & set(contract['required_facets']))
        settled, missing = {}, []
        for f in contract['required_facets']:
            if f in parsed['facts']:
                settled[f] = 'explicit'
            elif f in uncertain or f in parsed['conflicts']:
                continue
            elif self.defaults.get(f) == facts[f] and f not in parsed['uncertain_evidence'] and not MENTIONS[f].search(text):
                settled[f] = 'absent_add_on'
            else:
                missing.append(f)
        reason = ('facet_gate_conflict' if conflicts else 'facet_gate_contradiction' if contradictions else
                  'facet_gate_uncertain' if uncertain else 'facet_gate_missing' if missing else None)
        return dict(result, conflicts=conflicts, contradictions=contradictions, uncertain=uncertain,
                    missing=missing, settled=settled, accepted=reason is None, reason=reason)


class _Guarded:
    def __init__(self, approved, gate, statement):
        self.approved, self.gate, self.statement = approved, gate, statement

    def identity_check(self, entry, candidates, lookup, *, exact, minimum_margin):
        identity = self.approved.identity_check(entry, candidates, lookup, exact=exact, minimum_margin=minimum_margin)
        if exact or not identity['accepted']:
            return identity  # the exact-statement route and earlier rejections are unchanged
        guard = self.gate.check(self.statement, entry)
        result = dict(identity, facet_gate=guard)
        if not guard['accepted']:
            result.update(accepted=False, reason=guard['reason'])
        return result

    def check(self, entry):
        return self.approved.check(entry)


def answer_with_facet_gate(context, query, approved, gate):
    """Explicit experimental entry point; never enables generated fallback."""
    if approved is None:
        raise ValueError('Facet-gated recognition requires an approved library')
    from .answer import answer
    return answer(context, query, approved_library=_Guarded(approved, gate, query.statement))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('query', type=Path)
    parser.add_argument('--approved-library', type=Path, required=True)
    parser.add_argument('--contracts', type=Path, required=True)
    args = parser.parse_args()
    gate = FacetGate(json.loads(args.contracts.read_text()))
    from .approved_library import load_context
    from .records import Problem
    context, approved = load_context(args.approved_library)
    print(json.dumps(answer_with_facet_gate(context, Problem.from_dict(json.loads(args.query.read_text())), approved, gate),
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
