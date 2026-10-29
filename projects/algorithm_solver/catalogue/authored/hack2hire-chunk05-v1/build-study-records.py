"""Generate canonical teaching metadata; never changes the frozen test basis."""
from pathlib import Path
import hashlib
import json
from cases import build_cases, reference

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
OUT = HERE/'study-records'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer(name, selector=None):
    path = HERE/name
    return {'repository':'gamma','revision':None,'path':str(path.relative_to(ROOT)),'sha256':sha(path),'selector':selector}


def present(value, name, selector=None):
    return {'status':'present','value':value,'provenance':[pointer(name,selector)]}


def missing(reason):
    return {'status':'missing','reason':reason}


def unknown(reason):
    return {'status':'unknown','reason':reason}


def na(reason):
    return {'status':'not-applicable','reason':reason}


def file_ref(path, media):
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size,'mediaType':media}


def record(kind, id, name, selector=None, **fields):
    value = {'schema':'study.record.v1','kind':kind,'id':id,'version':1,'origin':[pointer(name,selector)],**fields}
    path = OUT/(kind+'--'+id.replace(':','_')+'.json')
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    return {'kind':kind,'id':id,'version':1,'path':str(path.relative_to(ROOT)),'sha256':sha(path)}


def artifact(id, title, pid, aid, contract, path, media, type, language, metadata):
    return record('artifact',id,str(path.relative_to(HERE)),type=type,title=title,problemId=pid,approachId=aid,contract=contract,file=present(file_ref(path,media),str(path.relative_to(HERE))),externalLocator=na('File belongs to this cohort'),language=language,documentSchema=None,executionKind='code' if type=='implementation' else 'reference-only',complexityClaims=present(metadata.pop('complexityClaims'),'design.json','/'+metadata['variant']) if 'complexityClaims' in metadata else na('Not an implementation'),nativeMetadata=present(metadata,str(path.relative_to(HERE))))


def main():
    OUT.mkdir(exist_ok=True)
    (HERE/'semantics').mkdir(exist_ok=True)
    contracts = json.loads((HERE/'contracts.json').read_text())['problems']
    designs = json.loads((HERE/'design.json').read_text())
    teaching = json.loads((HERE/'study-content.json').read_text())
    samples = {}
    for row in contracts:
        if row['key'] is None:
            continue
        first = build_cases(row['key'])[0]['args']
        if row['inferred_interface']['kind'] == 'class':
            first = [first[0][:5],first[1][:5]]
        samples[row['variant_id']] = [{'arguments':first,'expected':reference(row['key'],first),'scope':'Author-created example for inferred contract, not an official example'}]
    (HERE/'study-examples.json').write_text(json.dumps(samples,indent=2,ensure_ascii=False)+'\n')
    for index, row in enumerate(contracts):
        variant, pid = row['variant_id'], row['problemId']
        selector = '/problems/'+str(index)
        cid = 'contract:'+pid+':'+variant+':authored-v1'
        if row['key'] is None:
            record('contract',cid,'contracts.json',selector,problemId=pid,variantId=row['uid'],variantLabel=present(row['title'],'contracts.json',selector+'/title'),statement=missing(row['reason']),contentScope='unknown',requirements=missing('Defining requirements are omitted by the preview'),constraints=unknown('No exact variant specification'),assumptions=present([{'spec_basis':'inferred','status':'blocked','reason':row['reason']}],'contracts.json',selector),clarifyingQuestions=present([row['reason']],'contracts.json',selector+'/reason'),examples=missing('Cannot invent examples for an unavailable predicate'),interfaces=[],effects=unknown('No implementation authored'),comparison=unknown('No exact result contract'),sources=[],native=[])
            continue
        design, study = designs[variant], teaching[variant]
        interfaces = [{'language':lang,'kind':row['inferred_interface']['kind'],'declaration':present(row['inferred_interface'],'contracts.json',selector+'/inferred_interface'),'nativeMetadata':present({'spec_basis':'inferred','official_interface_available':False},'contracts.json',selector)} for lang in ('python','javascript')]
        contract = record('contract',cid,'contracts.json',selector,problemId=pid,variantId=row['uid'],variantLabel=present(row['title'],'contracts.json',selector+'/title'),statement=present(row['inferred_spec'],'contracts.json',selector+'/inferred_spec'),contentScope='authored',requirements=present([{'id':'r0','text':row['inferred_spec']},{'id':'r1','text':row['effects']}],'contracts.json',selector),constraints=present(study['constraints'],'study-content.json','/'+variant+'/constraints'),assumptions=present(study['assumptions'],'study-content.json','/'+variant+'/assumptions'),clarifyingQuestions=present(study['clarifyingQuestions'],'study-content.json','/'+variant+'/clarifyingQuestions'),examples=present(samples[variant],'study-examples.json','/'+variant),interfaces=interfaces,effects=present({'inputMutation':'forbidden','outputAliasing':'forbidden','classPrivateStateMutation':'allowed'},'contracts.json',selector+'/effects'),comparison=present({'kind':'exact','wire':'Integers within JavaScript safe range are numbers; larger exact integers encode as decimal strings. Python native integers and JS BigInt remain exact.'},'contracts.json',selector+'/comparison'),sources=[],native=[])
        aid = 'approach:'+pid+':'+variant+':v1'
        native = artifact('artifact:'+pid+':'+variant+':approach-native:v1','Authored design basis',pid,aid,contract,HERE/'design.json','application/json','source-native',None,{'variant':variant,'selector':'/'+variant,'spec_basis':'inferred','qualification':'unknown'})
        implementations = []
        for lang, suffix, media in [('python','py','text/x-python'),('javascript','js','text/javascript')]:
            source = HERE/lang/(variant+'.'+suffix)
            semantics = {'schema':'gamma.authored-native-semantics.v1','problem_id':row['uid'],'source_sha256':sha(source),'language':lang,'entrypoint':'solve','inferred_interface':row['inferred_interface'],'official_interface':None,'comparison':'exact typed result with lossless large-integer wire encoding','effects':row['effects'],'status':'unknown','qualification':{'status':'unknown','reason':'Author-local runs against inferred preview contracts only; no exact hidden-variant confirmation or independent qualification'},'source_reasoning':design,'numeric_semantics':'Python arbitrary-precision integers; JavaScript BigInt for grid counts, prime products, rational ratings and order quantities. Other input numeric fields are safe integers.','unicode_semantics':'Passwords use Unicode code points; board and remaining identifier/string domains follow the explicit ASCII/lowercase contracts.','assumptions':study['assumptions']}
            if row['key']=='lru':
                semantics['snapshot_cost']='Map recency operations are O(1); cloning a non-scalar stored value costs O(value size).'
            sem = HERE/'semantics'/(variant+'-'+lang+'.json'); sem.write_text(json.dumps(semantics,indent=2,ensure_ascii=False)+'\n')
            claims = [{'operation':'inferred exercise','target':design['complexity_target'],'assumptions':['Exact official bounds and largest-input suitability are unknown.','Integer arithmetic has bit cost; mutable-value cloning has value-size cost.'],'reasoning':design['candidate_design']}]
            implementations.append(artifact('artifact:'+pid+':'+variant+':'+lang+':v1',row['title']+' · '+lang,pid,aid,contract,source,media,'implementation',lang,{'variant':variant,'semantics':{'repository':'gamma','path':str(sem.relative_to(ROOT)),'sha256':sha(sem)},'qualification':'unknown','complexityClaims':claims}))
        suite = artifact('artifact:'+pid+':'+variant+':development-suite:v1','Frozen author development cases',pid,aid,contract,HERE/'cases.py','text/x-python','test-suite','python',{'variant':variant,'case_count':len(build_cases(row['key'])),'oracle':{'repository':'gamma','path':str((HERE/'oracles.py').relative_to(ROOT)),'sha256':sha(HERE/'oracles.py')},'scope':'Author-local development; not independent qualification'})
        stages = []
        for kind, question, explanation, artifacts, hints in [
            ('reasoning','Which rules are known and which remain inferred?',row['inferred_spec'],[],study['hints'][:1]),
            ('coding','Which invariant and data structure implement this exact contract?',design['candidate_design'],implementations,study['hints'][1:2]),
            ('validation','Which boundary or failed transition would falsify the implementation?','Compare each language independently with the frozen reference: '+design['reference']+' Local success applies only to the inferred contract; exact hidden-variant behavior, official resource limits and independent qualification remain unknown.',[suite],study['hints'][2:])
        ]:
            stages.append({'id':kind,'type':kind,'title':present(kind.title(),'design.json','/'+variant),'question':present(question,'study-content.json','/'+variant+'/clarifyingQuestions'),'explanation':present(explanation,'contracts.json' if kind=='reasoning' else 'design.json',selector+'/inferred_spec' if kind=='reasoning' else '/'+variant),'rationale':present('Separate the inferred contract, implementation choice and actual development evidence.','design.json','/'+variant),'instructions':present([design['candidate_design'] if kind=='coding' else question],'design.json','/'+variant),'observations':present([design['reference']] if kind=='validation' else [],'design.json','/'+variant),'hints':present(hints,'study-content.json','/'+variant+'/hints'),'requirementIds':present(['r0','r1'],'contracts.json',selector),'checks':[],'artifacts':artifacts,'native':native})
        record('approach',aid,'design.json','/'+variant,problemId=pid,contract=contract,title=present(design['candidate_design'],'design.json','/'+variant+'/candidate_design'),representation='coding',explanation=present(design['candidate_design'],'design.json','/'+variant+'/candidate_design'),chooseWhen=present(study['chooseWhen'],'study-content.json','/'+variant+'/chooseWhen'),tradeoffs=present(study['tradeoffs'],'study-content.json','/'+variant+'/tradeoffs'),invariants=present(study['invariants'],'study-content.json','/'+variant+'/invariants'),hints=present(study['hints'],'study-content.json','/'+variant+'/hints'),stages=stages,sequenceStatus='draft',native=native)
    print(json.dumps({'records':len(list(OUT.glob('*.json'))),'completed_pairs':36,'blocked_contracts':9}))


if __name__ == '__main__':
    main()
