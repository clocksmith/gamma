// AST data classification ONLY, never candidate execution or semantic admission.
import {acorn,scope} from '../ast-binding-alignment-v1/parser.mjs';
const methods=new Set(['get','set','has','add','delete','clear','keys','values','entries','forEach','push','pop','shift','unshift','reverse','sort','splice','slice','concat','indexOf','lastIndexOf','includes','join','fill','copyWithin','at','map','filter','reduce','some','every','find','findIndex','split','charAt','charCodeAt','substring','substr','startsWith','endsWith','replace','replaceAll','toLowerCase','toUpperCase','trim','match','test','exec','call','apply','bind','toString','valueOf','min','max','floor','ceil','abs']);
const globals=new Set(['Math','Map','Set','Array','String','Number','Object','JSON','RegExp','Date','Reflect','Proxy','Function','eval','parseInt','parseFloat','isNaN','Infinity','NaN','undefined']);
const mutators=new Set(['set','add','delete','clear','push','pop','shift','unshift','reverse','sort','splice','fill','copyWithin']);
function tree(ast){const nodes=[],parent=new Map();function walk(n,p){if(!n?.type)return;nodes.push(n);parent.set(n,p);for(const v of Object.values(n)){if(Array.isArray(v)){for(const x of v)if(x?.type)walk(x,n);}else if(v?.type)walk(v,n);}}walk(ast,null);return {nodes,parent};}
export function classify(source){
 const ast=acorn.parse(source,{ecmaVersion:2022,ranges:true});const {nodes,parent}=tree(ast);
 const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});
 const refs=new Map(),declarations=new Map();for(const s of manager.scopes){for(const r of s.references)refs.set(r.identifier,r);for(const v of s.variables)for(const d of v.defs)if(d.name)declarations.set(d.name,v);}
 const variable=n=>refs.get(n)?.resolved||declarations.get(n);
 const isGlobal=(n,name)=>n?.type==='Identifier'&&n.name===name&&refs.has(n)&&!refs.get(n).resolved;
 const prop=n=>n?.type==='MemberExpression'&&!n.computed&&n.property.type==='Identifier'?n.property.name:null;
 // Classification is deliberately conservative on assignment, alias and parameter
 // origin. Initializer shape is NOT a dominance, type, intrinsic or purity proof.
 function origin(n,seen=new Set()){
  if(!n)return 'unknown';
  if(n.type==='ArrayExpression')return 'array_literal';
  if(n.type==='ObjectExpression')return 'object_literal';
  if(n.type==='Literal')return n.regex?'regexp_literal':typeof n.value==='string'?'string_literal':typeof n.value==='number'?'number_literal':'other_literal';
  if(n.type==='NewExpression')return n.callee.type==='Identifier'&&isGlobal(n.callee,n.callee.name)&&['Map','Set','Array','RegExp'].includes(n.callee.name)?'new_'+n.callee.name:'other_constructor';
  if(n.type==='Identifier'){
   const v=variable(n);if(!v)return globals.has(n.name)&&isGlobal(n,n.name)?'global_'+n.name:'unresolved';
   if(seen.has(v))return 'alias_cycle';seen.add(v);
   if(v.defs.length!==1)return 'multiple_definitions';
   const d=v.defs[0];if(d.type==='Parameter')return 'parameter_unknown';
   if(d.type==='FunctionName')return 'local_function';
   if(v.references.some(r=>r.isWrite()&&!r.init))return 'reassigned_binding';
   if(d.type==='Variable'&&d.node.id.type==='Identifier'&&d.node.init)return origin(d.node.init,seen);
   return 'other_binding';
  }
  if(n.type==='MemberExpression')return 'member_result_unknown';
  if(n.type==='CallExpression')return 'call_result_unknown';
  return 'expression_unknown';
 }
 const counts={},inc=k=>counts[k]=(counts[k]||0)+1;let callCount=0;
 for(const n of nodes){
  if(n.type==='CallExpression'){
   callCount++;const c=n.callee;let category;
   if(c.type==='MemberExpression'){
    const name=prop(c);const receiver=origin(c.object);category='member/'+receiver+'/'+(name?(methods.has(name)?name:'other_named'):'computed');
    if(name&&mutators.has(name))inc('mutation_method/'+receiver+'/'+name);
    if(['call','apply','bind','toString','valueOf'].includes(name))inc('risk/reflection_or_indirect_call');
    if(c.computed)inc('risk/computed_callee');
   }else if(c.type==='Identifier'){
    const o=origin(c);category='direct/'+o;
    if(isGlobal(c,'eval')||isGlobal(c,'Function'))inc('risk/dynamic_code');
   }else category='call/other_expression';
   if(n.optional||c.optional)inc('risk/optional_call');inc(category);
   for(const arg of n.arguments)if(['FunctionExpression','ArrowFunctionExpression'].includes(arg.type)||arg.type==='Identifier'&&origin(arg)==='local_function')inc('risk/function_argument');
  }
  if(n.type==='NewExpression')inc('constructor/'+origin(n));
  if(n.type==='AssignmentExpression'||n.type==='UpdateExpression'||n.type==='UnaryExpression'&&n.operator==='delete'){
   const t=n.left||n.argument;
   if(t?.type==='MemberExpression'){inc('member_write/'+origin(t.object));let root=t;while(root.type==='MemberExpression')root=root.object;if(root.type==='Identifier'&&!variable(root))inc('risk/global_root_member_write');}
   else if(t?.type==='Identifier'&&refs.has(t)&&!variable(t))inc('risk/global_write');
  }
  if(n.type==='MemberExpression'&&methods.has(prop(n))&&!(parent.get(n)?.type==='CallExpression'&&parent.get(n).callee===n))inc('risk/method_reference_outside_direct_call');
  if(n.type==='MemberExpression'&&['prototype','__proto__','constructor','caller','callee','name'].includes(prop(n)))inc('risk/reflection_property');
  if(['WithStatement','ThisExpression','YieldExpression','AwaitExpression','ImportExpression'].includes(n.type))inc('risk/ambient_or_dynamic_syntax');
 }
 for(const [n,r]of refs)if(!r.resolved){
  inc('global_reference/'+(globals.has(n.name)?n.name:'other'));
  if(['eval','Function','Reflect','Proxy'].includes(n.name))inc('risk/reflective_global');
  if(['Map','Set','Array','Math','String','Number','Object','JSON','RegExp'].includes(n.name)){
   const p=parent.get(n);if(!(p?.type==='NewExpression'&&p.callee===n||p?.type==='MemberExpression'&&p.object===n||p?.type==='CallExpression'&&p.callee===n))inc('risk/intrinsic_object_escape');
  }
 }
 return {counts,call_count:callCount,admitted:false,origin_is_shape_not_type_or_dominance_proof:true};
}
export function controls(){
 const tests=[
 ['map','function solve(a){let m=new Map();return m.get(a);}','member/new_Map/get',1],
 ['set','function solve(a){let s=new Set();s.add(a);return s.has(a);}','member/new_Set/has',1],
 ['alias','function solve(a){let m=new Map(),n=m;return n.get(a);}','member/new_Map/get',1],
 ['shadow','function solve(Map){let m=new Map();return m.get(0);}','member/other_constructor/get',1],
 ['reassigned','function solve(a){let m=new Map();m=a;return m.get(0);}','member/reassigned_binding/get',1],
 ['parameter','function solve(a){return a.slice();}','member/parameter_unknown/slice',1],
 ['array','function solve(){let a=[];return a.push(1);}','member/array_literal/push',1],
 ['string','function solve(){return "x".split("");}','member/string_literal/split',1],
 ['nested','function solve(a){return a[0].slice();}','member/member_result_unknown/slice',1],
 ['globalwrite','function solve(a){Map.prototype.get=a;return 1;}','risk/global_root_member_write',1],
 ['reflection','function solve(a){return a.toString();}','risk/reflection_or_indirect_call',1],
 ['eval','function solve(a){return eval(a);}','risk/dynamic_code',1],
 ['optional','function solve(a){return a?.slice();}','risk/optional_call',1],
 ['callback','function solve(a){return a.map(x=>x);}','risk/function_argument',1],
 ['unknown','function solve(a){return a.privateName();}','member/parameter_unknown/other_named',1],
 ['escape','function solve(){let C=Map;return new C();}','risk/intrinsic_object_escape',1],
 ['methodreplacement','function solve(a){let m=new Map();m.get=a;return m.get(0);}','member_write/new_Map',1],
 ['conditional_shape_only','function solve(a){if(a){var m=new Map();}return m.get(0);}','member/new_Map/get',1]
 ];return tests.map(([name,source,key,expected])=>({name,key,expected,observed:classify(source).counts[key]||0}));
}
