"""Central structural graph contracts; editor/simulator semantics stay in Simulatte.

The imported composable-study schema is the starting compatibility contract. New
central changes regenerate TypeScript; legacy files in Simulatte remain unchanged
until consumer migration is approved. Semantic replay uses the existing command API.
"""
import copy,json
from pathlib import Path

def definitions():
 S={'type':'string'};V={'type':'number'};P={'type':'integer','minimum':1};J={};B={'type':'boolean'}
 def ref(n):return {'$ref':'#/$defs/'+n}
 def arr(x):return {'type':'array','items':x}
 def obj(p,req=None,extra=False):return {'type':'object','properties':p,'required':list(p) if req is None else req,'additionalProperties':extra}
 def en(*x):return {'enum':list(x)}
 def mapping(x):return {'type':'object','additionalProperties':x}
 D={
 'GraphEndpoint':obj({'nodeId':S,'portId':S}),
 'GraphPort':obj({'id':S,'direction':en('in','out'),'contractId':S}),
 'GraphPosition':obj({'x':V,'y':V}),
 'ArchitectureNode':obj({'id':S,'label':S,'componentId':S,'componentVersion':P,'parentId':S,'boundaryId':S,'lineageIds':arr(S),'groupId':{'type':['string','null']}},['id','label','componentId','componentVersion']),
 'ArchitectureEdge':obj({'id':S,'from':ref('GraphEndpoint'),'to':ref('GraphEndpoint'),'contractId':S,'mode':en('request-response','event-stream','storage','local-call','message'),'label':S},['id','from','to','contractId','mode']),
 'ArchitectureGroup':obj({'id':S,'label':S,'kind':S,'capacity':P},['id','label','kind']),
 'GraphContract':obj({'id':S,'version':P,'request':J,'response':J},['id'],True),
 'GraphComponent':obj({'id':S,'version':P,'ports':arr(ref('GraphPort'))},['id','version'],True),
 'GraphBoundary':obj({'id':S,'componentId':S,'componentVersion':P,'ports':arr(obj({'id':S,'direction':en('in','out'),'contractId':S,'target':ref('GraphEndpoint')}))}),
 }
 D['ArchitectureDefinitions']=obj({'contracts':arr(ref('GraphContract')),'components':arr(ref('GraphComponent')),'boundaries':arr(ref('GraphBoundary'))})
 D['ArchitectureGraph']=obj({'nodes':arr(ref('ArchitectureNode')),'edges':arr(ref('ArchitectureEdge')),'groups':arr(ref('ArchitectureGroup'))})
 D['ArchitectureModel']=obj({'schema':{'const':'simulatte.architecture.v1'},'id':S,'name':S,'description':S,'definitions':ref('ArchitectureDefinitions'),'graph':ref('ArchitectureGraph'),'simulation':{'type':['object','null']},'presentation':obj({'lucyd':mapping(J),'study':mapping(J)},[])},['schema','id','name','definitions','graph','simulation','presentation'])
 commands=[]
 def command(op,props,required=None):commands.append(obj({'op':{'const':op},**props},['op']+(list(props) if required is None else required)))
 command('insert',{'node':ref('ArchitectureNode'),'positions':mapping(ref('GraphPosition'))},['node'])
 command('remove',{'nodeId':S});command('connect',{'edge':ref('ArchitectureEdge')});command('disconnect',{'edgeId':S})
 command('reconnect',{'edgeId':S,'edge':ref('ArchitectureEdge'),'reason':S})
 command('replace',{'nodeId':S,'componentId':S,'componentVersion':P,'label':S,'migration':S},['nodeId','componentId','migration'])
 command('expand',{'nodeId':S,'boundaryId':S,'nodes':arr(ref('ArchitectureNode')),'edges':arr(ref('ArchitectureEdge')),'positions':mapping(mapping(ref('GraphPosition')))},['nodeId','boundaryId','nodes','edges'])
 command('rebind',{'nodeId':S,'boundaryId':S,'reason':S})
 command('merge',{'nodeIds':{'type':'array','minItems':2,'uniqueItems':True,'items':S},'node':ref('ArchitectureNode'),'reason':S,'positions':mapping(ref('GraphPosition'))},['nodeIds','node','reason'])
 command('relabel',{'nodeId':S,'label':S});command('regroup',{'nodeId':S,'groupId':{'type':['string','null']}},['nodeId']);command('setGroups',{'groups':arr(ref('ArchitectureGroup'))})
 command('move',{'nodeId':S,'view':en('lucyd','study'),'x':V,'y':V});command('bind',{'nodeId':S,'binding':mapping(J)});command('unbind',{'nodeId':S})
 D['ArchitectureCommand']={'oneOf':commands}
 D['ArchitectureTransition']=obj({'schema':{'const':'study.architectureTransition.v1'},'before':ref('ArchitectureModel'),'operations':arr(ref('ArchitectureCommand')),'after':ref('ArchitectureModel')})
 D['SimulationNode']=obj({'id':S,'classId':S,'label':S,'x':V,'y':V,'params':mapping(J),'groupId':{'type':['string','null']},'overrides':mapping(J)},['id','classId','label','x','y','params'])
 D['SimulationEdge']=obj({'id':S,'from':ref('GraphEndpoint'),'to':ref('GraphEndpoint'),'params':mapping(J),'label':S},['id','from','to','params'])
 D['SimulationGroup']=obj({'id':S,'label':S,'kind':en('zone','region','boundary','resource'),'x':V,'y':V,'w':{'type':'number','exclusiveMinimum':0},'h':{'type':'number','exclusiveMinimum':0},'capacity':{'type':'integer','minimum':1,'maximum':64},'collapsed':B},['id','label','kind','x','y','w','h'])
 D['SimulationNote']=obj({'id':S,'text':S,'x':V,'y':V,'w':V},['id','text','x','y'])
 D['SimulationFault']=obj({'id':S,'atSec':{'type':'number','minimum':0},'untilSec':{'type':['number','null']},'target':obj({'kind':en('node','edge','group'),'id':S}),'type':S,'params':mapping(J)})
 D['SimulationClass']=obj({'id':S,'label':S,'extends':S,'defaults':mapping(J),'category':S,'glyph':S,'description':S},['id','label','extends','defaults'])
 D['SimulationSubsystem']=obj({'id':S,'version':P,'label':S,'nodes':arr(ref('SimulationNode')),'edges':arr(ref('SimulationEdge')),'groups':arr(ref('SimulationGroup')),'notes':arr(ref('SimulationNote')),'faults':arr(ref('SimulationFault')),'ports':arr(obj({'id':S,'label':S,'direction':en('in','out'),'target':ref('GraphEndpoint')}))})
 base={'id':S,'name':S,'description':S,'seed':{'type':'integer','minimum':0,'maximum':4294967295},'run':obj({'horizonSec':{'type':'number','exclusiveMinimum':0}}),'classes':arr(ref('SimulationClass')),'nodes':arr(ref('SimulationNode')),'edges':arr(ref('SimulationEdge')),'groups':arr(ref('SimulationGroup')),'notes':arr(ref('SimulationNote')),'faults':arr(ref('SimulationFault')),'view':obj({'x':V,'y':V,'zoom':{'type':'number','exclusiveMinimum':0}}),'subsystems':arr(ref('SimulationSubsystem'))}
 required=[k for k in base if k not in ('description','subsystems')]
 D['SimulationDiagramV4']=obj({'schema':{'const':'simulatte.systemDiagram.v4'},**base},['schema']+required)
 D['ConceptResponsibility']=obj({'id':S,'label':S,'responsibility':S,'ports':arr(obj({'id':S,'direction':en('in','out'),'payloadType':S})),'binding':obj({'classId':S,'ports':mapping(S)})},['id','label','responsibility','ports'])
 D['SimulationDiagramV5']=obj({'schema':{'const':'simulatte.systemDiagram.v5'},**base,'intent':obj({'outcome':S,'users':S,'constraints':S,'success':S}),'concepts':arr(ref('ConceptResponsibility'))},['schema']+required+['concepts'])
 # Consolidate the full existing study schema without dropping its native fields.
 native=json.loads((Path(__file__).parent/'legacy/composable-study.v2.schema.json').read_text())
 def rename(value):
  if isinstance(value,dict):return {k:('#/$defs/Study_'+v.split('/')[-1] if k=='$ref' and v.startswith('#/$defs/') else rename(v)) for k,v in value.items() if k not in ('$schema','$defs')}
  if isinstance(value,list):return [rename(v) for v in value]
  return value
 for name,value in native.get('$defs',{}).items():D['Study_'+name]=rename(value)
 D['ComposableStudyDocument']=rename(native)
 return D
