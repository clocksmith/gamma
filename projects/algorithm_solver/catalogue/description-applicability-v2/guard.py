"""Versioned, deliberately partial applicability guard. No model or source reads.

Facts are contract/query clauses, not problem identities. Unrecognized language
is UNKNOWN. This module never closes the open world or qualifies recognition.
"""
from dataclasses import dataclass, asdict
import hashlib
import json
import re

from projects.algorithm_solver.catalogue.interpretation_gate import Facet
from projects.algorithm_solver.catalogue.facet_bitset import FacetBitsetIndex
from projects.algorithm_solver.catalogue.empirical_recognition import decide, rank
from projects.algorithm_solver.catalogue.recognition_documents import pinned_metadata, sha
from projects.algorithm_solver.catalogue.boundary_policy import authorize_before_open

VERSION = 'gamma.description-applicability.v2'
FACETS = ('result_shape', 'returned_entity', 'selection', 'graph_direction',
          'input_order', 'input_distinctness', 'input_mutation', 'output_alias')
SHAPES = {'int':'scalar-integer', 'integer':'scalar-integer', 'bool':'boolean',
          'boolean':'boolean', 'str':'string', 'string':'string', 'real':'real',
          'array<integer>':'integer-array', 'list[int]':'integer-array',
          'integer[]':'integer-array', 'integer[2]':'integer-array',
          'array<string>':'string-array', 'array<array<integer>>':'integer-matrix'}

@dataclass(frozen=True)
class Evidence:
    facet: str
    value: str
    field: str
    start: int
    end: int
    span: str
    text_sha256: str
    rule: str


def evidence(text, facet, value, field, start, end, rule):
    return Evidence(facet, value, field, start, end, text[start:end],
                    sha(text.encode()), rule)


def facts(items):
    """Conflicting evidence is not resolved by ordering or last-write-wins."""
    values = {}
    for item in items:
        values.setdefault(item.facet, set()).add(item.value)
    conflicts = sorted(k for k,v in values.items() if len(v)>1)
    return {k:next(iter(v)) for k,v in values.items() if len(v)==1}, conflicts


# Anchored full-clause grammar. Never substring-scan arbitrary natural language:
# negations, quotations, conditionals and coordination cannot silently invert it.
QUERY_RULES = (
    (r'(?:return|output) (?:the )?(?:minimum |maximum |nearest |smallest |largest )?(?:value|values)', 'returned_entity', 'value'),
    (r'(?:return|output) (?:the )?(?:minimum |maximum |nearest |smallest |largest )?(?:index|indices)', 'returned_entity', 'index'),
    (r'(?:return|output) all (?:matching )?(?:values|elements)', 'returned_entity', 'value'),
    (r'(?:return|output) all (?:matching )?indices', 'returned_entity', 'index'),
    (r'(?:return|output) (?:one|a single) (?:matching )?(?:value|element)', 'returned_entity', 'value'),
    (r'(?:return|output) (?:one|a single) (?:matching )?index', 'returned_entity', 'index'),
    (r'(?:return|output) all (?:matching )?(?:values|elements|indices)', 'selection', 'all'),
    (r'(?:return|output) (?:one|a single) (?:matching )?(?:value|element|index)', 'selection', 'one'),
    (r'(?:the )?graph is directed', 'graph_direction', 'directed'),
    (r'(?:the )?graph is undirected', 'graph_direction', 'undirected'),
    (r'(?:the )?input array is sorted', 'input_order', 'sorted'),
    (r'(?:the )?input array is (?:arbitrary|not necessarily sorted|unsorted)', 'input_order', 'arbitrary'),
    (r'(?:the )?input array is rotated sorted', 'input_order', 'rotated-sorted'),
    (r'(?:the )?input mutation is required', 'input_mutation', 'required'),
    (r'(?:do not mutate (?:the )?input|(?:the )?input mutation is forbidden)', 'input_mutation', 'forbidden'),
    (r'(?:return|output) a new array', 'output_alias', 'fresh'),
    (r'(?:return|output) (?:the )?same input array', 'output_alias', 'input'),
    (r'(?:return|output) (?:a |an )?boolean', 'result_shape', 'boolean'),
    (r'(?:return|output) (?:a |an )?integer', 'result_shape', 'scalar-integer'),
    (r'(?:return|output) (?:a )?string', 'result_shape', 'string'),
    (r'(?:return|output) (?:an )?integer array', 'result_shape', 'integer-array'),
    (r'(?:the )?input array is strictly ascending', 'input_order', 'sorted'),
    (r'(?:the )?input array is strictly ascending', 'input_distinctness', 'distinct'),
    (r'(?:the )?input array is rotated strictly ascending', 'input_order', 'rotated-sorted'),
    (r'(?:the )?input array is rotated strictly ascending', 'input_distinctness', 'distinct'),
    (r'(?:the )?input elements are distinct', 'input_distinctness', 'distinct'),
)


def parse_query(text):
    if type(text) is not str or not text.strip() or len(text.encode())>32768:
        raise ValueError('nonempty bounded query required')
    items=[]; unsupported=[]
    for match in re.finditer(r'[^.;\n]+',text):
        start,end=match.span()
        while start<end and text[start].isspace(): start+=1
        while end>start and text[end-1].isspace(): end-=1
        if start==end: continue
        clause=text[start:end]; found=False
        for i,(pattern,facet,value) in enumerate(QUERY_RULES):
            if re.fullmatch(pattern,clause,re.I|re.ASCII):
                items.append(evidence(text,facet,value,'query',start,end,f'query-{i}'));found=True
        if not found: unsupported.append({'start':start,'end':end,'span':clause})
    known,conflicts=facts(items)
    return {'facts':known,'conflicts':conflicts,'evidence':[asdict(x) for x in items],
            'unsupported_spans':unsupported,
            'grammar_complete':bool(items) and not unsupported and not conflicts,
            'query_sha256':sha(text.encode()),'semantic_proof':False}


def contract_facts(doc):
    """Consumes only already-gated whitelisted document text, never titles.

    Typed result domains are structured authority. Objective adapters are exact
    anchored clauses, not generic lexical overlap or per-problem ID lookups.
    Mutation effects not present in these documents remain unknown.
    """
    text=doc['text']; items=[]; fields={}
    for match in re.finditer(r'^(Objective|Result|Input domain|Ordered interface): (.+)$',text,re.M):
        fields[match[1]]=(json.loads(match[2]),match.start(2),match.end(2))
    def add(facet,value,label,rule):
        _,start,end=fields[label]
        items.append(evidence(text,facet,value,label,start,end,rule))
    if not fields: return {'facts':{},'conflicts':[],'evidence':[]}
    result=fields.get('Result',({},0,0))[0]
    typ=result.get('type',result.get('domain')) if isinstance(result,dict) else None
    if isinstance(typ,dict): typ=typ.get('type')
    if isinstance(typ,str) and typ in SHAPES: add('result_shape',SHAPES[typ],'Result','structured-result-type')
    objective=fields.get('Objective',('',0,0))[0]
    domain=fields.get('Input domain',({},0,0))[0]
    if isinstance(objective,str):
        for pattern, facet,value in (
            (r'Minimum input element\.', 'returned_entity','value'),
            (r'Duplicate value first, missing value second\.', 'returned_entity','value'),
            (r'Return the first i with .+, or -1\.', 'returned_entity','index'),
            (r'Return the nearest reachable drone index .+; return -1 if none\.', 'returned_entity','index'),
            (r'Return the first i with .+, or -1\.', 'selection','one'),
            (r'Return the nearest reachable drone index .+; return -1 if none\.', 'selection','one'),
            (r'Exactly the words in words1 containing, for every word in words2, at least its count of each letter\.', 'selection','all'),
            (r'For each node index, return every distinct predecessor reachable by a positive-length directed path to it, numerically ascending\.', 'selection','all'),
            (r'Return a new array containing the original elements followed by the reversed elements\.', 'output_alias','fresh'),
        ):
            if re.fullmatch(pattern,objective): add(facet,value,'Objective','anchored-objective-'+facet)
    if isinstance(domain,dict):
        if domain.get('distinct') is True:
            add('input_distinctness','distinct','Input domain','structured-distinctness')
        graph=domain.get('graph')
        if graph=='undirected, no parallel edges': add('graph_direction','undirected','Input domain','structured-graph')
        if graph=='directed acyclic, no duplicate edges': add('graph_direction','directed','Input domain','structured-graph')
        if domain.get('structure')=='A strictly ascending array rotated right between 1 and n times, inclusive.':
            add('input_order','rotated-sorted','Input domain','structured-rotation')
        if domain.get('derived_element_range')=='1 through n, from set construction; input need not be sorted.':
            add('input_order','arbitrary','Input domain','explicit-unrestricted-order')
    known,conflicts=facts(items)
    return {'facts':known,'conflicts':conflicts,'evidence':[asdict(x) for x in items],
            'authority_sha256':doc.get('authority',{}).get('authority_sha256'),
            'document_sha256':sha(text.encode())}


def compare(query, contract):
    """UNKNOWN differs from VIOLATED. SATISFIED means these facets only."""
    verdicts={}
    for facet in FACETS:
        q=query['facts'].get(facet); c=contract['facts'].get(facet)
        if facet in query['conflicts'] or facet in contract['conflicts'] or q is None or c is None:
            verdict=Facet.UNKNOWN
        elif facet=='input_order' and c=='arbitrary':
            verdict=Facet.SATISFIED  # Order facet only; no distinctness assertion.
        elif facet=='input_order' and c=='rotated-sorted' and q in ('sorted','rotated-sorted'):
            # The admitted rotation adapter is STRICT/distinct. Ordinary sorted
            # or rotated-sorted descriptions allow duplicates, so inclusion is
            # unknown without an independently parsed distinctness premise.
            verdict=(Facet.SATISFIED if query['facts'].get('input_distinctness')=='distinct'
                     and 'input_distinctness' not in query['conflicts'] else Facet.UNKNOWN)
        elif q==c: verdict=Facet.SATISFIED
        else: verdict=Facet.VIOLATED
        verdicts[facet]=verdict
    overall=(Facet.VIOLATED if Facet.VIOLATED in verdicts.values() else
             Facet.UNKNOWN if Facet.UNKNOWN in verdicts.values() else Facet.SATISFIED)
    return {'overall':overall.value,'facets':{k:v.value for k,v in verdicts.items()},
            'contradictions':[k for k,v in verdicts.items() if v is Facet.VIOLATED],
            'semantic_proof':False}


def load_documents(plan_spec, document_spec):
    """All statement permissions are checked BEFORE opening the combined file.

    Inputs are operator pins, not request fields. No referenced source is opened.
    """
    plan=pinned_metadata(plan_spec); gate=pinned_metadata(plan['boundary_gate'])
    allowed={row['problem_id'] for row in plan['authorities']}
    for pid in sorted(allowed):
        authorize_before_open(pid,gate['artifact_paths'],gate['trusted_hashes'],language='python',payload_kind='statement')
    bundle=pinned_metadata(document_spec)
    if bundle['plan_sha256']!=plan_spec['sha256']: raise ValueError('plan binding mismatch')
    ids=bundle['stable_ids']
    if len(ids)!=plan['expected_population'] or len(set(ids))!=len(ids): raise ValueError('population mismatch')
    if [r['problem_id'] for r in bundle['documents']]!=ids: raise ValueError('document identity/order mismatch')
    out={}
    for row in bundle['documents']:
        pid=row['problem_id']
        if sha(row['text'].encode())!=row['document_sha256']: raise ValueError('document hash mismatch')
        if pid not in allowed:
            if row['authority']['knowledge_class']!='title-only' or '\n' in row['text']:
                raise ValueError('non-authorized semantic content')
            out[pid]={'facts':{},'conflicts':[],'evidence':[]}
        else: out[pid]=contract_facts(row)
    return ids,out


def filter_candidates(ids, contracts, parsed):
    """Reuse exact finite bitsets only for symmetric categorical contradictions.

    Input-order entailment is asymmetric, so handled by compare, not bitsets.
    Outside-catalogue risk is deliberately NOT discharged.
    """
    if not parsed['grammar_complete']: return frozenset(ids)
    compatible={pid:{k:v for k,v in contracts[pid]['facts'].items() if k!='input_order'} for pid in ids}
    query={k:v for k,v in parsed['facts'].items() if k!='input_order'}
    kept=FacetBitsetIndex(ids,compatible).candidates(query)
    return frozenset(pid for pid in kept if not compare(parsed,contracts[pid])['contradictions'])


def guarded_decide(text, ranked, policy, service, ids, contracts, *, truncated=False):
    """Prospective veto-only composition with the ORIGINAL threshold family.

    Never rerank after a veto or use source availability to choose a runner-up.
    Unrestricted prose can reach only empirical acceptance, never grammar proof.
    Unknown facts do not veto; their unresolved status accompanies the result.
    """
    if len(ranked)!=len(ids) or {r[0] for r in ranked}!=set(ids) or set(contracts)!=set(ids):
        raise ValueError('complete unchanged competitor population required')
    if list(ranked)!=rank([r[1] for r in ranked],[r[0] for r in ranked]):
        raise ValueError('canonical complete ranking required; guard never reranks')
    parsed=parse_query(text); report=compare(parsed,contracts[ranked[0][0]])
    if parsed['conflicts'] or report['contradictions']:
        return {'status':'abstain','reason':'description_facet_conflict',
                'clarification_questions':[],'semantic_proof':False,'guard':report,'query_analysis':parsed}
    result=decide(ranked,policy,service,truncated=truncated)
    return dict(result,guard=report,query_analysis=parsed,guard_version=VERSION,
                recognition_qualified=False,semantic_proof=False)
