"""Conservative development grammar for explicit requirement spans.

This recognizes only declared phrases; silence never supplies a requirement.
It is not a general natural-language model. Keep conflicting evidence visible.
"""
import re


# (facet, value, positive evidence). Patterns are development-only, not fitted
# to the independently authored evaluation. All returned facts retain spans.
RULES = [
    ('family','pair',r'\b(?:two numbers|pair of|two positions)\b'),
    ('family','houses',r'\bhouses?\b'),
    ('family','stock',r'\b(?:stock|trades?|trading)\b'),
    ('family','courses',r'\b(?:courses?|prerequisites)\b'),
    ('family','land',r'\b(?:land|islands?)\b'),
    ('family','frequency',r'\b(?:most often|most frequent|highest frequencies)\b'),
    ('family','rank',r'\b(?:kth|rank-th|third) largest\b'),
    ('family','window',r'\bconsecutive slice\b'),
    ('ordering','arbitrary',r'\b(?:unsorted|not sorted|no sorted[- ]order guarantee)\b'),
    ('ordering','sorted',r'(?<!not )\bsorted (?:in ascending|in nondecreasing|input|array)\b'),
    ('indexing','zero',r'\bzero[- ]based positions\b'),
    ('indexing','one',r'\b(?:one[- ]based positions|counting positions from one)\b'),
    ('output','positions',r'\b(?:two (?:zero-based )?positions|two (?:zero-based )?indices|return the two positions)\b'),
    ('layout','line',r'\b(?:straight (?:street|line)|houses in a line)\b'),
    ('layout','circle',r'\b(?:closed block|circle of houses|houses in a circle|last house touches the first)\b'),
    ('layout','tree',r'\bbinary tree\b'),
    ('output','cash',r'\b(?:maximum cash|largest total from houses|maximum total cash)\b'),
    ('transactions','one',r'\b(?:buy once|one (?:completed )?(?:trade|transaction))\b'),
    ('transactions','two',r'\bat most two (?:completed )?(?:trades|transactions)\b'),
    ('transactions','unlimited',r'\b(?:repeatedly buy|any number of stock trades|as often as I want|unlimited (?:trades|transactions))\b'),
    ('fee','none',r'\b(?:no fees?|no transaction fee)\b'),
    ('fee','per_trade',r'\b(?:costs commission|charged once per (?:completed )?trade|transaction fee of)\b'),
    ('cooldown','none',r'\b(?:no cooldown|no (?:fees or )?waiting days?)\b'),
    ('cooldown','one_day',r'\b(?:sit out the next day|wait the next day after|one[- ]day cooldown)\b'),
    ('output','profit',r'\b(?:maximum (?:total |net )?profit|most profit|biggest profit)\b'),
    ('output','possible',r'\b(?:true or false|whether (?:all|every) courses? can be completed)\b'),
    ('output','order',r'\breturn any ordering\b'),
    ('output','count',r'\b(?:return their count|number of separate land|how many separate land)\b'),
    ('output','area',r'\b(?:biggest connected patch|largest component|largest island)\b'),
    ('output','frequent',r'\b(?:which k distinct values occur most often|k most frequent distinct)\b'),
    ('output','kth',r'\b(?:kth|rank-th) largest\b'),
    ('updates','batch',r'\b(?:one fixed array|one fixed input|in items|in this array)\b'),
    ('updates','stream',r'\b(?:after each insertion|stream of)\b'),
    ('duplicates','occurrences',r'\bcounting duplicate occurrences separately\b'),
    ('duplicates','distinct',r'\b(?:third distinct|count each distinct value once)\b'),
    ('changes','none',r'\b(?:without adding land|no cell changes|do not (?:add|change) land)\b'),
    ('changes','one_flip',r'\b(?:change at most one zero to one|flip one zero)\b'),
    ('output','length',r'\b(?:return its length|minimum qualifying slice length)\b'),
    ('output','sum',r'\b(?:return that sum|largest sum of a nonempty)\b'),
]


def extract(text):
    evidence = {}
    for facet,value,pattern in RULES:
        for match in re.finditer(pattern,text,re.I):
            prefix = re.split(r'[.;!?\n]',text[:match.start()])[-1][-60:]
            if value not in ('none','arbitrary') and re.search(
                    r"\b(?:not|never|don't|do not|no)\s+(?:\w+\s+){0,3}$",prefix,re.I):
                continue
            evidence.setdefault(facet,{}).setdefault(value,[]).append({
                'start':match.start(),'end':match.end(),'text':match.group()})
    facts = {facet:next(iter(values)) for facet,values in evidence.items() if len(values)==1}
    conflicts = {facet:values for facet,values in evidence.items() if len(values)>1}
    return {'facts':facts, 'conflicts':conflicts, 'evidence':evidence,
            'scope':'explicit development grammar; unrecognized prose remains unchecked'}
