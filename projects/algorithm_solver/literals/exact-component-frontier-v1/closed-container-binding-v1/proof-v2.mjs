// Restricted alpha-equivalence investigation owner. Never evaluates source text.
import {acorn,scope} from '../ast-binding-alignment-v1/parser.mjs';
import {strictSubset,compareResolution} from '../ast-binding-alignment-v1/alignment.mjs';
import {numericIndexProof} from '../ast-binding-alignment-v1/numeric-index-proof-v2.mjs';
import {canonicalize} from '../ast-binding-alignment-v1/canonicalize.mjs';
const methods={array:new Set(['push','pop']),Map:new Set(['get','set','has']),Set:new Set(['add','has','delete'])};
export function containerSubset(source){
 const ast=acorn.parse(source,{ecmaVersion:2022,ranges:true}),nodes=[],parents=new Map();
 function walk(n,p){if(!n?.type)return;nodes.push(n);parents.set(n,p);for(const v of Object.values(n)){if(Array.isArray(v)){for(const c of v)if(c?.type)walk(c,n);}else if(v?.type)walk(v,n);}}walk(ast,null);
 const reasons=new Set(strictSubset(source).reasons.filter(x=>!['unsupported_CallExpression','unsupported_NewExpression','non_length_named_property','unresolved_global_reference','string_or_regex_value'].includes(x)));
 const functions=nodes.filter(n=>['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression'].includes(n.type));
 const solve=ast.body.length===1&&ast.body[0].type==='FunctionDeclaration'&&ast.body[0].id.name==='solve'?ast.body[0]:null;
 if(!solve||functions.length!==1)reasons.add('single_solve_without_local_helpers_required');
 const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false}),refs=new Map(),decls=new Map(),variables=[];
 for(const s of manager.scopes){for(const r of s.references)refs.set(r.identifier,r);for(const v of s.variables){variables.push(v);for(const d of v.defs)if(d.name)decls.set(d.name,v);}}
 const variable=n=>refs.get(n)?.resolved||decls.get(n);
 const global=(n,name)=>n?.type==='Identifier'&&n.name===name&&refs.has(n)&&!refs.get(n).resolved;
 const property=n=>n?.type==='MemberExpression'&&!n.computed&&!n.optional&&n.property.type==='Identifier'?n.property.name:null;
 const functionOf=n=>{let p=n;while(p&&!['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression'].includes(p.type))p=parents.get(p);return p;};
 // Local lexical names can appear in TDZ ReferenceError messages. Reject
 // uncertain execution order, independently of fresh-container dominance.
 for(const v of variables)for(const d of v.defs){
  if(d.type==='Parameter'&&d.node.params.some(n=>n.type!=='Identifier'))reasons.add('non_simple_parameter_initialization');
  if(d.type!=='Variable')continue;
  const decl=parents.get(d.node),placement=parents.get(decl);
  if(!['let','const'].includes(decl?.kind))continue;
  if(d.node.id.type!=='Identifier'){reasons.add('destructuring_lexical_initialization');continue;}
  const point=d.node.init?d.node.init.end:d.node.end;
  const initialRef=r=>r.init&&r.identifier===d.node.id;
  const functionBody=functionOf(d.node);
  if(placement?.type==='BlockStatement'){
   if(v.references.some(r=>!initialRef(r)&&(functionOf(r.identifier)!==functionBody||r.identifier.start<point)))reasons.add('lexical_TDZ_or_capture');
  }else if(placement?.type==='ForStatement'&&placement.init===decl){
   if(v.references.some(r=>!initialRef(r)&&(functionOf(r.identifier)!==functionBody||r.identifier.start<point||r.identifier.start<placement.start||r.identifier.end>placement.end)))reasons.add('lexical_loop_TDZ_or_escape');
  }else if(placement?.type==='ForOfStatement'&&placement.left===decl){
   if(v.references.some(r=>!initialRef(r)&&(functionOf(r.identifier)!==functionBody||r.identifier.start<placement.body.start||r.identifier.end>placement.body.end)))reasons.add('lexical_forof_TDZ_or_escape');
  }else reasons.add('lexical_initialization_placement_unproved');
 }
 const mathCallee=n=>property(n)&&global(n.object,'Math')&&['min','max'].includes(property(n));
 const directCallMember=n=>parents.get(n)?.type==='CallExpression'&&parents.get(n).callee===n&&!parents.get(n).optional;
 function dominates(v,d){
  const declaration=parents.get(d.node);
  if(!solve||d.node.type!=='VariableDeclarator'||d.node.id.type!=='Identifier'||declaration?.type!=='VariableDeclaration'||parents.get(declaration)!==solve.body){reasons.add('container_initializer_not_unconditional_function_body');return false;}
  if(v.references.some(r=>r.isWrite()&&!r.init)){reasons.add('container_binding_reassigned');return false;}
  if(v.references.some(r=>!(r.init&&r.identifier===d.node.id)&&(functionOf(r.identifier)!==solve||r.identifier.start<d.node.init.end))){reasons.add('container_initializer_not_dominating_all_references');return false;}
  return true;
 }
 function origin(n,seen=new Set()){
  if(n?.type==='ArrayExpression')return 'array';
  if(n?.type==='NewExpression'&&n.arguments.length===0){if(global(n.callee,'Map'))return 'Map';if(global(n.callee,'Set'))return 'Set';}
  if(n?.type!=='Identifier')return null;
  const v=variable(n);if(!v||seen.has(v)||v.defs.length!==1)return null;seen.add(v);
  const d=v.defs[0];if(d.type!=='Variable'||!d.node.init)return null;
  const kind=origin(d.node.init,seen);if(!kind)return null;
  return dominates(v,d)?kind:null;
 }
 let containerCalls=0,mathCalls=0;const kinds={array:0,Map:0,Set:0};
 for(const v of variables){
  if(v.defs.length&&['Map','Set','Math'].includes(v.name))reasons.add('shadowed_intrinsic_binding');
  if(v.defs.length===1&&v.defs[0].type==='Variable'&&v.defs[0].node.id.type==='Identifier'){
   const kind=origin(v.defs[0].node.id);if(kind)kinds[kind]++;
  }
 }
 for(const [n,r]of refs)if(!r.resolved){
  const p=parents.get(n);
  const constructor=['Map','Set'].some(name=>global(n,name))&&p?.type==='NewExpression'&&p.callee===n&&p.arguments.length===0;
  const math=global(n,'Math')&&p?.object===n&&mathCallee(p)&&directCallMember(p);
  if(!constructor&&!math)reasons.add('unresolved_or_escaped_global');
 }
 for(const n of nodes){
  if(['ChainExpression','ObjectExpression','TryStatement','CatchClause','ThrowStatement','ForInStatement','ObjectPattern','ArrayPattern','AssignmentPattern'].includes(n.type))reasons.add('unsupported_'+n.type);
  if(n.type==='Literal'&&n.regex)reasons.add('regex_not_in_container_core');
  if(n.type==='NewExpression'&&!origin(n))reasons.add('only_zero_argument_direct_Map_Set_construction');
  if(n.type==='CallExpression'){
   if(n.optional||n.callee.optional)reasons.add('optional_call');
   if(mathCallee(n.callee)&&!n.optional&&n.arguments.length>=1){mathCalls++;continue;}
   const name=property(n.callee),kind=n.callee.type==='MemberExpression'?origin(n.callee.object):null;
   if(!kind||!methods[kind].has(name)||n.optional||n.callee.optional)reasons.add('nonclosed_container_callee');
   else{
    containerCalls++;
    const arities={push:null,pop:0,get:1,set:2,has:1,add:1,delete:1};
    if(arities[name]!==null&&n.arguments.length!==arities[name])reasons.add('unsupported_core_method_arity');
   }
  }
  if(n.type==='MemberExpression'&&!n.computed){
   const name=property(n),kind=origin(n.object);
   const isMethod=directCallMember(n)&&(mathCallee(n)||kind&&methods[kind].has(name));
   if(!isMethod&&name!=='length'&&!(name==='size'&&['Map','Set'].includes(kind)))reasons.add('method_escape_or_unsupported_property');
  }
  if(n.type==='AssignmentExpression'||n.type==='UpdateExpression'||n.type==='UnaryExpression'&&n.operator==='delete'){
   const target=n.left||n.argument;
   if(n.operator==='delete')reasons.add('delete_operator');
   if(target?.type==='MemberExpression'){
    if(!target.computed)reasons.add('named_property_mutation');
    if(['Map','Set'].includes(origin(target.object)))reasons.add('collection_property_mutation');
   }
   if(target?.type==='ArrayPattern'||target?.type==='ObjectPattern')reasons.add('destructuring_assignment_not_in_core');
  }
 }
 if(containerCalls===0)reasons.add('no_closed_container_feature');
 const index=numericIndexProof(source);if(!index.all_computed_indices_inductively_numeric)reasons.add('unproved_computed_index');
 return {syntactic_candidate:reasons.size===0,reasons:[...reasons].sort(),container_calls:containerCalls,math_calls:mathCalls,proven_immutable_container_bindings:kinds,admitted:false,qualification:false,
  required_external_proof:'Exact source/finite original cases/effects: plain JSON inputs with no functions/accessors/proxies; numeric computed indices; fresh unmodified Array/Map/Set/Math intrinsic prototypes; full matched original/format/role replay. No container algorithm or numerical transformation; source eligibility alone is not admission.'};
}
// Only a structural postcondition for an externally authorized transform; this
// module intentionally provides no private-source transformation admission API.
export function checkAlphaPostcondition(source,transformed){return compareResolution(source,transformed);}
export function syntheticAlphaControl(source){const subset=containerSubset(source);if(!subset.syntactic_candidate)throw Error('synthetic source outside subset');for(const mode of ['format','role']){const out=canonicalize(source,mode);checkAlphaPostcondition(source,out.source);}return true;}
