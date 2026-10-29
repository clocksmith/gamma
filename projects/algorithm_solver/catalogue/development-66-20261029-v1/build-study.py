"""Add study-record extensions without rewriting another session's run receipts."""
from pathlib import Path
import hashlib
import importlib.util
import json
from lessons import LESSONS
from run import COHORTS, ROOT

HERE=Path(__file__).resolve().parent


def raw(value):return (json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pointer(path,selector=None):return {'repository':'gamma','revision':None,'path':str(path.relative_to(ROOT)),'sha256':sha(path),'selector':selector}
def present(value,path,selector=None):return {'status':'present','value':value,'provenance':[pointer(path,selector)]}
def missing(reason):return {'status':'missing','reason':reason}
def unknown(reason):return {'status':'unknown','reason':reason}
def na(reason):return {'status':'not-applicable','reason':reason}
def file_ref(path,media):return {'path':str(path.relative_to(ROOT)),'sha256':sha(path),'bytes':path.stat().st_size,'mediaType':media}
def keep(path,value):
    data=raw(value)
    if path.exists() and path.read_bytes()!=data:raise RuntimeError('Existing authored extension differs; preserve it and review an explicit revision: '+str(path))
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)


def build(base):
    out=base/'study-records';out.mkdir(exist_ok=True)
    contracts=json.loads((base/'contracts.json').read_text())['problems'];designs=json.loads((base/'design.json').read_text())['problems']
    design_by_id={row['id']:(i,row) for i,row in enumerate(designs)}
    spec=importlib.util.spec_from_file_location('study_cases_'+base.name.replace('-','_'),base/'cases.py');cases=importlib.util.module_from_spec(spec);spec.loader.exec_module(cases)
    content={};examples={};written=[]
    for row in contracts:
        pid=row['id'];statement,invariant,nudge,pitfall=LESSONS[pid];i,design=design_by_id[pid];mechanism=design['numeric_complexity_contract']['candidate_design']
        content[str(pid)]={'author':'Codex','authoredAt':'2026-10-29','scope':'Authored study paraphrase from the existing source-declared interface, candidate design and cohort cases; original private statement not re-read or reverified.','statement':statement,'requirements':[{'id':'r0','text':statement},{'id':'r1','text':'The declared JSON solve wrapper preserves its input arguments and returns the cohort result representation.'}],'constraints':{'status':'unknown','reason':'The complete original statement bounds have not been normalized or independently checked; retain the existing validate_domain and its source claims separately.'},'assumptions':['This record preserves a specific authored cohort contract, not a newly verified official specification.','The JSON wrapper and the source-declared native interface may have different serialization and ownership rules.'],'clarifyingQuestions':['Which exact output order, tie, numeric and mutation rules does the target interface require?','Does the full intended input domain match the cohort domain validator?'],'explanation':mechanism+' '+invariant+' '+pitfall,'invariant':invariant,'hints':[nudge,invariant,mechanism,pitfall],'chooseWhen':[nudge,'Use the stated invariant only when the problem and interface assumptions hold.'],'tradeoffs':[pitfall,'The existing complexity target is an inherited claim, not an independent measurement; wrapper serialization may add memory.'],'stages':[
          {'id':'reasoning','title':'Establish the invariant','question':nudge,'explanation':statement+' '+invariant,'rationale':'Identify the information that must survive each step before choosing code.','instructions':['State the input/output contract.', 'Explain why the invariant is sufficient.'],'hints':[nudge]},
          {'id':'coding','title':'Implement the state transition','question':'Which state changes make the next step preserve this invariant?','explanation':mechanism+' '+invariant,'rationale':pitfall,'instructions':[mechanism,'Keep JSON-wrapper effects distinct from native object effects.'],'hints':[invariant,mechanism]},
          {'id':'validation','title':'Challenge the boundary','question':'What boundary or counterexample would expose this mistake?','explanation':pitfall+' Check the returned value and input ownership independently. The existing base and extended cases cover selected examples; they do not establish complete domain coverage or native-interface compatibility.','rationale':'A successful sample run is not a substitute for a contract and counterexamples.','instructions':['Run both languages against the pinned cohort cases.', 'Inspect numeric, order and ownership assumptions separately.'],'hints':[pitfall]}
        ]}
        generated=cases.build_cases(pid,include_maximum=False)
        examples[str(pid)]=[{'arguments':case['args'],'expected':case['expected'],'source':'cohort-authored development example; not asserted to be an official example'} for case in generated[:2]]
    content_path=base/'study-content.json';example_path=base/'study-examples.json';keep(content_path,content);keep(example_path,examples)
    def record(kind,id,origin,selector=None,**fields):
        value={'schema':'study.record.v1','kind':kind,'id':id,'version':1,'origin':[pointer(origin,selector)],**fields};path=out/(kind+'--'+id.replace(':','_')+'.json');keep(path,value);written.append(path)
        return {'kind':kind,'id':id,'version':1,'path':str(path.relative_to(ROOT)),'sha256':sha(path)}
    def artifact(id,title,pid,aid,contract,path,media,type,language,metadata,selector=None):
        return record('artifact',id,path,selector,type=type,title=title,problemId=pid,approachId=aid,contract=contract,file=present(file_ref(path,media),path),externalLocator=na('Cohort-owned file'),language=language,documentSchema=None,executionKind='code' if type=='implementation' else 'reference-only',complexityClaims=unknown('The inherited complexity target requires separate review; native and JSON-wrapper allocation costs differ.') if type=='implementation' else na('Not an implementation'),nativeMetadata=present(metadata,path,selector))
    for index,row in enumerate(contracts):
        number=row['id'];pid='leetcode:'+str(number);variant=base.name+':'+str(number);lesson=content[str(number)];prefix='/'+str(number);ci='/problems/'+str(index);di,design=design_by_id[number];ds='/problems/'+str(di)
        cid='contract:'+pid+':'+variant+':authored-v1';aid='approach:'+pid+':'+variant+':v1';iface=row['official_interface'];declaration=iface
        if number==911:declaration={'classname':'TopVotedCandidate','constructor':iface,'methods':[{'name':'q','params':[{'name':'t','type':'integer'}],'return':'integer'}],'scope':'cohort-declared class trace'}
        contract=record('contract',cid,base/'contracts.json',ci,problemId=pid,variantId=variant,variantLabel=present(row['title'],base/'contracts.json',ci+'/title'),statement=present(lesson['statement'],content_path,prefix+'/statement'),contentScope='authored',requirements=present(lesson['requirements'],content_path,prefix+'/requirements'),constraints=unknown(lesson['constraints']['reason']),assumptions=present(lesson['assumptions'],content_path,prefix+'/assumptions'),clarifyingQuestions=present(lesson['clarifyingQuestions'],content_path,prefix+'/clarifyingQuestions'),examples=present(examples[str(number)],example_path,prefix),interfaces=[{'language':lang,'kind':'class' if number==911 else 'function','declaration':present(declaration,base/'contracts.json',ci+'/official_interface'),'nativeMetadata':present({'scope':'Existing source-declared ABI retained; native compatibility is not established by the JSON-wrapper runs.','originalDeclaration':iface},base/'contracts.json',ci+'/official_interface')} for lang in ('python','javascript')],effects=present({'scope':'JSON solve wrapper','inputMutation':'forbidden','outputAliasing':'forbidden','nativeObjectEffects':'not-established-by-wrapper-execution'},base/'design.json',ds+'/mutation_alias_contract'),comparison=present({'kind':'exact','scope':'Existing cohort deterministic JSON result; native nonunique/float acceptance policy requires separate confirmation.'},base/'design.json',ds+'/return_domain'),sources=[],native=[])
        native=artifact('artifact:'+pid+':'+variant+':approach-native:v1',row['title']+' design basis',pid,aid,contract,base/'design.json','application/json','source-native',None,{'selector':ds,'scope':'Unmodified author design and inherited targets'},ds)
        implementations=[]
        for language,suffix,media in [('python','py','text/x-python'),('javascript','js','text/javascript')]:
            source=base/language/(str(number)+'.'+suffix);sem=base/'semantics'/(str(number)+'-'+language+'.json')
            implementations.append(artifact('artifact:'+pid+':'+variant+':'+language+':v1',row['title']+' · '+language,pid,aid,contract,source,media,'implementation',language,{'sourceSha256':sha(source),'semantics':{'repository':'gamma','path':str(sem.relative_to(ROOT)),'sha256':sha(sem)},'qualification':'unknown','nativeAbiStatus':'not-established-by-json-wrapper-tests'}))
        suite=artifact('artifact:'+pid+':'+variant+':development-suite:v1',row['title']+' development cases',pid,aid,contract,base/'cases.py','text/x-python','test-suite','python',{'oracle':{'repository':'gamma','path':str((base/'oracles.py').relative_to(ROOT)),'sha256':sha(base/'oracles.py')},'scope':'Cohort author base/extended references; not independent qualification'})
        stages=[]
        for si,stage in enumerate(lesson['stages']):
            sp=prefix+'/stages/'+str(si);artifacts=implementations if stage['id']=='coding' else [suite] if stage['id']=='validation' else []
            stages.append({'id':stage['id'],'type':stage['id'],'title':present(stage['title'],content_path,sp+'/title'),'question':present(stage['question'],content_path,sp+'/question'),'explanation':present(stage['explanation'],content_path,sp+'/explanation'),'rationale':present(stage['rationale'],content_path,sp+'/rationale'),'instructions':present(stage['instructions'],content_path,sp+'/instructions'),'observations':missing('No interactive study observations authored'),'hints':present(stage['hints'],content_path,sp+'/hints'),'requirementIds':present(['r0','r1'],content_path,prefix+'/requirements'),'checks':[],'artifacts':artifacts,'native':native})
        record('approach',aid,content_path,prefix,problemId=pid,contract=contract,title=present(design['numeric_complexity_contract']['candidate_design'],base/'design.json',ds+'/numeric_complexity_contract/candidate_design'),representation='coding',explanation=present(lesson['explanation'],content_path,prefix+'/explanation'),chooseWhen=present(lesson['chooseWhen'],content_path,prefix+'/chooseWhen'),tradeoffs=present(lesson['tradeoffs'],content_path,prefix+'/tradeoffs'),invariants=present([lesson['invariant']],content_path,prefix+'/invariant'),hints=present(lesson['hints'],content_path,prefix+'/hints'),stages=stages,sequenceStatus='draft',native=native)
    guide=base/'STUDY.md'
    text='# Study-record extension\n\n'+str(len(contracts))+' problems; one authored approach and three ordered stages per problem. Each has problem framing, invariant, hints, examples and pinned Python/JavaScript references.\n\nThe source contracts, existing oracles and candidates are preserved. Paraphrases are authored from cohort metadata and cases, not copied official statements. Complete bounds and native-interface compatibility remain unverified; no evidence or admission records are created. The source-defined extended cases are not asserted to be official domain maxima.\n\nValidate with `python3 test_study_records.py` and `shasum -a 256 -c STUDY-SHA256SUMS`. The study extension has its own manifest and hashes so concurrent development-run receipts are not overwritten.\n'
    if guide.exists() and guide.read_text()!=text:raise RuntimeError('Existing study guide differs')
    guide.write_text(text)
    written.extend([content_path,example_path,guide])
    test=base/'test_study_records.py'
    test_text='from pathlib import Path\nimport importlib.util\nROOT=Path(__file__).resolve().parents[5]\np=ROOT/"projects/algorithm_solver/catalogue/development-66-20261029-v1/validate-study.py"\ns=importlib.util.spec_from_file_location("validate_authored_study",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nif __name__=="__main__":m.validate(Path(__file__).resolve().parent)\n'
    if test.exists() and test.read_text()!=test_text:raise RuntimeError('Existing study validation entrypoint differs')
    test.write_text(test_text);written.append(test)
    manifest=base/'study-manifest.json';keep(manifest,{'schema':'gamma.authored-study-extension.v1','cohort':base.name,'problems':len(contracts),'approaches':len(contracts),'stages':len(contracts)*3,'records':len(list(out.glob('*.json'))),'qualification':'unknown','files':[{'path':str(p.relative_to(base)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(written)]});written.append(manifest)
    sums=base/'STUDY-SHA256SUMS';sums.write_text(''.join(sha(p)+'  '+str(p.relative_to(base))+'\n' for p in sorted(written)))
    print(base.name,len(contracts),'problems',len(list(out.glob('*.json'))),'records')


if __name__=='__main__':
    for cohort in COHORTS:build(ROOT/'projects/algorithm_solver/catalogue/authored'/cohort)
