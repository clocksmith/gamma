"""Rebuild local candidate metadata and content hashes; never qualify or execute sources."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json

ROOT=Path(__file__).resolve().parent

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def canonical(obj):return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def write(name,obj):(ROOT/name).write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def load(name):
    spec=importlib.util.spec_from_file_location('gamma_requested589_metadata_'+name,ROOT/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def build():
    o,c=load('oracles'),load('cases')
    contracts=json.loads((ROOT/'contracts.json').read_text())['problems'];design=json.loads((ROOT/'design.json').read_text())['problems']
    assignment=[];sources=[];case_summary={}
    reference_notes={589:'recursive child-list concatenation',590:'recursive child-list concatenation',600:'enumerate all admissible binary strings',606:'recursive literal parenthesis rendering',617:'recursive tuple-tree merge',622:'literal list queue model',623:'recursive tuple-tree insertion and explicit maximum node-table construction',629:'permutation inversion census; Euler pentagonal coefficient for maximum',630:'all course subsets with deadline feasibility',632:'Cartesian product of list selections',637:'recursive depth buckets and exact sums',639:'enumerate matching numeric tokenizations; matrix exponentiation at maximum',641:'literal list deque model',652:'literal subtree tuple census per root',653:'all node-value pairs',654:'recursive maximum scans',655:'recursive height and interval placement',662:'complete binary path strings with arbitrary precision',664:'BFS over every overwritten interval and print character',671:'distinct-value order statistic',675:'Floyd-Warshall all-pairs shortest paths',676:'all dictionary words, count positional mismatches',677:'literal key dictionary with prefix filtering',679:'all leaf permutations, binary expression-tree splits, exact fractions',687:'all-start equal-value graph distances; two-sweep diameter at maximum',689:'enumerate nonoverlapping index triples',690:'fixed-point subordinate reachability',699:'coordinate-compressed occupied-cell heights',700:'flat node lookup and literal subtree serialization',701:'sorted contents plus independent strict BST observer',703:'literal accumulated values sorted after each add',705:'independent built-in set model',706:'independent built-in dictionary model',707:'literal Python list operations',710:'literal allowed support and exhaustive small ticket bijection checks',715:'set of covered unit cells on bounded domains',719:'sort all pairwise distances',721:'repeated email-set connected-component closure',725:'literal contiguous slices and remainder distribution'}
    for row in contracts:
        pid=row['id'];official=row['official_interface'];isclass=pid in o.CLASSES
        parameters=['operations','arguments'] if isclass else [p['name'] for p in official['params'] if not p.get('lang')]
        comparison='absolute tolerance1e-5 on level averages' if pid==637 else 'unordered distinct subtree serializations' if pid==652 else 'strict BST and exact inorder contents' if pid==701 else 'unordered account groups, exact sorted emails' if pid==721 else 'valid random support; exhaustive small injected-ticket bijection, no cross-language random-sequence comparison' if pid==710 else 'exact typed result under documented object transport'
        alias='fresh output nodes, disjoint from input and other output parts' if pid in (617,623,654,701,725) else 'existing input subtree roots may be returned unchanged' if pid in (652,700) else 'fresh result containers or immutable scalar; internal class state may change'
        reasoning={**design[str(pid)],'reference':reference_notes[pid]}
        interface={'canonical':'solve','argument_order':parameters,'language_parameter_names':{'python':parameters,'javascript':['operations','args'] if isclass else parameters},'official':official}
        native='binary tree: queue-order nullable array; solve receives native .val/.left/.right nodes' if pid in o.TREE_IDS else 'N-ary root: values/children index table in development transport; solve receives native .val/.children nodes' if pid in (589,590) else 'employee triples converted to native .id/.importance/.subordinates objects' if pid==690 else 'list values converted to native .val/.next nodes; output parts observed as value arrays' if pid==725 else 'class operation trace preserving constructor/method parameter order' if isclass else 'JSON values in official parameter order'
        entry={'id':pid,'title':row['title'],'slug':row['slug'],'external_interface':interface,'comparison':{'policy':comparison},'mutation_alias_contract':{'arguments':'unchanged','return':alias},'numeric_complexity_contract':reasoning,'return_domain':official.get('return',{}),'qualification_status':'unknown','statement_constraints_snapshot':{'domain_owner':'oracles.py validate_domain','full_text_location':'local ignored projects/algorithm_solver/data/authoring/continuation-data-structures39-20261028-v1/'+str(pid)+'.json','response_sha256':row['response_sha256']},'transport':native}
        assignment.append(entry)
        for lang,ext in [('python','py'),('javascript','js')]:
            source=f'{lang}/{pid}.{ext}';sem=f'semantics/{pid}-{lang}.json'
            value={'schema':'gamma.authored-object-semantics.v1','problem_id':pid,'language':lang,'entrypoint':'solve','parameters':parameters,'official_interface':official,'comparison':comparison,'effects':'arguments unchanged; '+alias,'qualification':{'status':'unknown','reason':'Finite local development checks only; no independent isolated qualification or adoption'},'source_reasoning':reasoning,'candidate_design':reasoning['candidate_design'],'complexity_target':reasoning['complexity_target'],'source_sha256':digest(ROOT/source),'transport':native}
            if pid in (589,590,690):value['manual_metadata_type_note']='Official metaData uses a manual placeholder type; native object ABI follows the pinned official code stub and documented transport.'
            write(sem,value);sources.append({'id':pid,'language':lang,'path':source,'sha256':digest(ROOT/source),'semantics_path':sem,'semantics_sha256':digest(ROOT/sem)})
        rows=c.build_cases(pid,True);case_summary[str(pid)]={'bounded_cases':sum(r['category']=='independent-bounded-reference' for r in rows),'maximum_cases':sum(r['category']=='analytic-maximum' for r in rows),'maximum_rationales':[r['rationale'] for r in rows if r['category']=='analytic-maximum'],'reference':reference_notes[pid]}
    write('assignment.public-safe.json',{'schema':'gamma.authored-assignment.v1','problems':assignment,'authorization':'Explicit owner39-ID request; pinned metadata gate passed for both languages before exact official public statement acquisition; protected cases remain closed.','status':'candidate authoring; no qualification or adoption'})
    write('case-design-summary.json',{'schema':'gamma.independent-case-design.v1','problems':case_summary,'candidate_source_imports_in_reference':False,'source_free_initial_freeze':'Historical initial reference hashes retained; folder collision required independent reference reconstruction after draft. See reference-recovery.json.','scope':'development-only generated cases; no protected or private benchmark cases'})
    excluded={'manifest.json','SHA256SUMS','authoring-catalog.json'}
    files=[{'path':str(p.relative_to(ROOT)),'sha256':digest(p)} for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name not in excluded]
    manifest={'schema':'gamma.authored-sources-manifest.v1','assignment_sha256':digest(ROOT/'assignment.public-safe.json'),'files':files,'sources':sources,'status':'78 authored candidates; finite local development checks are not qualification'}
    write('manifest.json',manifest)
    variants=[];index={}
    for source in sources:
        pid,lang=source['id'],source['language'];contract=next(r for r in assignment if r['id']==pid);variant={'problem_id':pid,'language':lang,'source_sha256':source['sha256'],'semantics_sha256':source['semantics_sha256'],'problem_contract_sha256':canonical(contract),'qualification':{'status':'unknown','reason':'No independent qualification receipt'},'provenance':[{'source_path':source['path'],'semantics_path':source['semantics_path'],'manifest_sha256':digest(ROOT/'manifest.json'),'assignment_sha256':digest(ROOT/'assignment.public-safe.json')}]};variant['variant_id']=canonical(variant);variants.append(variant);index.setdefault(str(pid),{}).setdefault(lang,[]).append(variant['variant_id'])
    write('authoring-catalog.json',{'schema':'gamma.authoring-variant-catalog-pilot.v1','unique_problem_count':len(contracts),'variant_count':len(variants),'variants':variants,'index':index,'preferred_variant':None,'qualification_policy':'Unknown only. This cohort accepts no qualification receipts and confers no admission.'})
    paths=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='SHA256SUMS']
    (ROOT/'SHA256SUMS').write_text(''.join(digest(p)+'  '+str(p.relative_to(ROOT))+'\n' for p in paths))
    print('Metadata rebuilt:',len(contracts),'problems;',len(sources),'sources;',sum(v['bounded_cases']+v['maximum_cases'] for v in case_summary.values()),'cases per language')
if __name__=='__main__':build()
