"""One declarative JSON Schema authority; TypeScript is generated from this subset."""
import json
from pathlib import Path

S={'type':'string'}
N={'type':'integer','minimum':0}
P={'type':'integer','minimum':1}
SHA={'type':'string','pattern':'^[a-f0-9]{64}$'}
ID={'type':'string','minLength':1}
J={}  # Opaque JSON is permitted only in preserved source-native metadata.

def ref(name):return {'$ref':'#/$defs/'+name}
def array(item):return {'type':'array','items':item}
def enum(*items):return {'enum':list(items)}
def obj(properties,required=None):return {'type':'object','additionalProperties':False,'properties':properties,'required':list(properties) if required is None else required}
def field(value):return {'oneOf':[obj({'status':{'const':'present'},'value':value,'provenance':{'type':'array','minItems':1,'items':ref('SourcePointer')}}),obj({'status':{'const':'missing'},'reason':S}),obj({'status':{'const':'unknown'},'reason':S}),obj({'status':{'const':'not-applicable'},'reason':S})]}

KINDS=('problem','contract','approach','artifact','evidence','source','company','company-report','relationship','admission')
D={
 'SourcePointer':obj({'repository':S,'revision':{'type':['string','null']},'path':S,'sha256':SHA,'selector':{'type':['string','null']}}),
 'Ref':obj({'kind':enum(*KINDS),'id':ID,'version':P,'path':S,'sha256':SHA}),
 'FileRef':obj({'path':S,'sha256':SHA,'bytes':N,'mediaType':S}),
 'TextField':field(S),'ListField':field(array(J)),'JsonField':field(J),
 'Interface':obj({'language':S,'kind':enum('function','class','sql','unknown'),'declaration':field(J),'nativeMetadata':ref('JsonField')}),
 'Stage':obj({'id':ID,'type':enum('reasoning','coding','design','validation','simulation'),'title':ref('TextField'),'question':ref('TextField'),'explanation':ref('TextField'),'rationale':ref('TextField'),'instructions':ref('ListField'),'observations':ref('ListField'),'hints':ref('ListField'),'requirementIds':ref('ListField'),'checks':array(ref('Ref')),'artifacts':array(ref('Ref')),'native':ref('Ref')}),
}
BASE={'kind':enum(*KINDS),'id':ID,'version':P,'schema':{'const':'study.record.v1'},'origin':{'type':'array','minItems':1,'items':ref('SourcePointer')}}
SPEC={
 'problem':{'title':ref('TextField'),'type':enum('coding','system-design','sql','ml-design','ood','unknown'),'topics':ref('ListField'),'difficulty':ref('JsonField'),'aliases':array(J),'contracts':array(ref('Ref')),'approaches':array(ref('Ref')),'artifacts':array(ref('Ref')),'evidence':array(ref('Ref')),'sources':array(ref('Ref')),'companyReports':array(ref('Ref')),'relationships':array(ref('Ref')),'identity':obj({'status':enum('source-declared','reviewed','unresolved'),'explanation':S})},
 'contract':{'problemId':ID,'variantId':ID,'variantLabel':ref('TextField'),'statement':ref('TextField'),'contentScope':enum('full-statement','preview','authored','unknown'),'requirements':ref('ListField'),'constraints':ref('ListField'),'assumptions':ref('ListField'),'clarifyingQuestions':ref('ListField'),'examples':ref('ListField'),'interfaces':array(ref('Interface')),'effects':ref('JsonField'),'comparison':ref('JsonField'),'sources':array(ref('Ref')),'native':array(ref('Ref'))},
 'approach':{'problemId':ID,'contract':ref('Ref'),'title':ref('TextField'),'representation':enum('coding','conceptual-design','simulation','unknown'),'explanation':ref('TextField'),'chooseWhen':ref('ListField'),'tradeoffs':ref('ListField'),'invariants':ref('ListField'),'hints':ref('ListField'),'stages':array(ref('Stage')),'sequenceStatus':enum('imported','draft','study-ready'),'native':ref('Ref')},
 'artifact':{'type':enum('implementation','diagram','graph-change','code-change','api-contract','workload','fault-schedule','test-suite','check','runtime','adapter','pseudocode','source-native','integration-reference'),'title':S,'problemId':{'type':['string','null']},'approachId':{'type':['string','null']},'contract':{'anyOf':[ref('Ref'),{'type':'null'}]},'file':field(ref('FileRef')),'externalLocator':ref('JsonField'),'language':{'type':['string','null']},'documentSchema':{'type':['string','null']},'executionKind':enum('conceptual','simulation','code','reference-only','unknown'),'complexityClaims':ref('ListField'),'nativeMetadata':ref('JsonField')},
 'evidence':{'contract':{'anyOf':[ref('Ref'),{'type':'null'}]},'subjects':array(ref('Ref')),'method':enum('historical-report','execution','manual-review','simulation','measured-operation','model-generated-suggestion'),'bindingStatus':enum('bound','partial','unbound'),'bindings':ref('JsonField'),'results':ref('JsonField'),'report':ref('Ref'),'limitations':array(S),'admissionEffect':{'const':'none'}},
 'source':{'title':S,'url':{'type':['string','null']},'publisher':ref('TextField'),'sourceType':S,'contentScope':enum('metadata','preview','full','reference-only'),'license':ref('TextField'),'redistribution':enum('permitted','prohibited','unknown'),'native':ref('Ref')},
 'company':{'name':S,'aliases':array(S),'website':ref('TextField')},
 'company-report':{'company':ref('Ref'),'contract':ref('Ref'),'source':ref('Ref'),'claim':enum('asked-in-interview','published-practice-question','company-inspired-practice','unresolved'),'attribution':enum('company-published','candidate-reported','aggregator-reported','authored-practice','unverified'),'frequency':ref('JsonField'),'reportedAt':ref('TextField'),'role':ref('TextField'),'nativeMetadata':ref('JsonField')},
 'admission':{'target':ref('Ref'),'contract':ref('Ref'),'purpose':enum('observer-reference','solver-reference','study-publication','simulation-execution','deployment-release'),'decision':enum('approved','rejected','blocked','retired'),'decidedBy':S,'decidedAt':S,'evidence':array(ref('Ref')),'explanation':S,'limitations':array(S)},
 'relationship':{'fromContract':ref('Ref'),'to':ref('JsonField'),'relation':enum('related','variant-of','source-cites','title-match-candidate','reviewed-contract-equivalent'),'explanation':S,'sources':array(ref('Ref')),'evidence':array(ref('Ref')),'mergeAllowed':{'const':False}},
}
for kind,props in SPEC.items():D[kind.title().replace('-','')]=obj({**BASE,'kind':{'const':kind},**props})
# Derived embedding contracts share the same generated type/schema authority.
D['EncoderIdentity']=obj({'modelId':S,'modelRevision':S,**{k:SHA for k in ('modelManifestSha256','tokenizerManifestSha256','adapterSha256','runtimeManifestSha256')},'pooling':S,'normalization':enum('none','l2'),'dtype':S,'documentInstruction':S,'queryInstruction':S,'maxTokens':P,'truncation':S})
D['EmbeddingRecipe']=obj({'chunker':{'const':'codepoint-window-v1'},'maxCharacters':{'const':1200},'overlapCharacters':{'const':100}})
D['EncoderContract']=obj({'schema':{'const':'study.encoder-contract.v1'},'command':{'type':'array','minItems':1,'items':S},'commandFile':S,'commandFileSha256':SHA,'encoderIdentity':ref('EncoderIdentity'),'recipe':ref('EmbeddingRecipe'),'dimensions':P})
D['EmbeddingEntry']=obj({'id':ID,'purpose':enum('problem-discovery','solution-study','artifact-search'),'owner':ref('Ref'),'field':S,'chunkOrdinal':N,'textSha256':SHA,'vectorRow':N})
D['EmbeddingIndex']=obj({'schema':{'const':'study.embedding-index.v1'},'purpose':enum('problem-discovery','solution-study','artifact-search'),'encoderFingerprint':SHA,'encoderProgramSha256':SHA,'encoderIdentity':ref('EncoderIdentity'),'recipe':ref('EmbeddingRecipe'),'dimensions':P,'encoding':{'const':'float32-le'},'distance':enum('cosine','dot-product'),'entries':array(ref('EmbeddingEntry')),'vectors':ref('FileRef'),'access':S})
D['EmbeddingRelease']=obj({'schema':{'const':'study.embedding-release.v1'},'indexes':array(ref('FileRef'))})

from graphs import definitions as graph_definitions
D.update(graph_definitions())
SCHEMA={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'urn:deco:study-record:v1','$defs':D,'oneOf':[ref(k.title().replace('-','')) for k in KINDS]}


def typescript(node,depth=0):
 if not node:return 'Json'
 if '$ref' in node:return node['$ref'].split('/')[-1]
 if 'const' in node:return json.dumps(node['const'])
 if 'enum' in node:return ' | '.join(json.dumps(v) for v in node['enum'])
 for key in ('oneOf','anyOf'):
  if key in node:return ' | '.join('('+typescript(v,depth)+')' for v in node[key])
 t=node.get('type')
 if isinstance(t,list):return ' | '.join(typescript({'type':v},depth) for v in t)
 if t=='null':return 'null'
 if t in ('number','integer'):return 'number'
 if t in ('string','boolean'):return t
 if t=='array':return 'ReadonlyArray<'+typescript(node['items'],depth)+'>'
 if t=='object':
  properties=node.get('properties',{});extra=node.get('additionalProperties',True);pad='  '*(depth+1)
  fixed=[pad+json.dumps(k)+('' if k in node.get('required',[]) else '?')+': '+typescript(v,depth+1)+';' for k,v in properties.items()]
  if extra is True:fixed.append(pad+'[key: string]: Json | undefined;')
  elif isinstance(extra,dict):fixed.append(pad+'[key: string]: '+typescript(extra,depth+1)+';')
  return '{\n'+'\n'.join(fixed)+'\n'+'  '*depth+'}'
 if t is None:return 'Json'
 raise ValueError(node)


def generate(directory=None):
 directory=Path(directory or Path(__file__).parent)
 (directory/'schema.v1.json').write_text(json.dumps(SCHEMA,indent=2,sort_keys=True)+'\n')
 content='// GENERATED from schema.py. Edit its declarative definitions, then regenerate.\n// Partial fields are migration facts; these types do not assert runtime validation.\nexport type Json = null | boolean | number | string | ReadonlyArray<Json> | { readonly [key: string]: Json };\n'
 content+='\n'.join('export type '+name+' = '+typescript(value)+';\n' for name,value in D.items())
 content+='\nexport type StudyRecord = '+' | '.join(k.title().replace('-','') for k in KINDS)+';\n'
 content+='\nexport type LucydGraphDocument = ArchitectureModel | SimulationDiagramV4 | SimulationDiagramV5 | ComposableStudyDocument;\n'
 (directory/'schema.v1.ts').write_text(content)

if __name__=='__main__':generate()
