// Source-as-data only. No candidate eval, calls, imports, or transformation.
import {acorn,scope} from '../ast-binding-alignment-v1/parser.mjs';
const numericMath=new Set(['abs','ceil','floor','round','trunc','min','max','sqrt','cbrt','pow','sign','clz32','imul','fround','hypot','log','log2','log10','exp','expm1','log1p','sin','cos','tan','asin','acos','atan','atan2','sinh','cosh','tanh','asinh','acosh','atanh']);
const arrayNames=new Set(['push','pop','shift','unshift','reverse','sort','splice','slice','concat','indexOf','lastIndexOf','includes','join','fill','copyWithin','at']);
const mutatingNames=new Set(['push','pop','shift','unshift','reverse','sort','splice','fill','copyWithin']);
function nodesOf(ast){const out=[],parents=new Map();function walk(n,p){if(!n||!n.type)return;out.push(n);parents.set(n,p);for(const v of Object.values(n)){if(Array.isArray(v)){for(const x of v)if(x?.type)walk(x,n);}else if(v?.type)walk(v,n);}}walk(ast,null);return {out,parents};}
export function classify(source){
 const ast=acorn.parse(source,{ecmaVersion:2022,ranges:true});const {out,parents}=nodesOf(ast);const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});
 const refs=new Map();for(const s of manager.scopes)for(const r of s.references)refs.set(r.identifier,r);
 const global=(n,name)=>n?.type==='Identifier'&&n.name===name&&refs.has(n)&&!refs.get(n).resolved;
 const property=n=>n?.type==='MemberExpression'&&!n.computed&&n.property.type==='Identifier'?n.property.name:null;
 const count={};const inc=k=>count[k]=(count[k]||0)+1;const calls=[];
 for(const n of out){
  if(n.type==='CallExpression'){
   const c=n.callee,name=property(c);let category;
   if(c.type==='MemberExpression'&&global(c.object,'Math'))category=name&&numericMath.has(name)?'direct_numeric_Math.'+name:'other_or_dynamic_Math_call';
   else if(c.type==='MemberExpression'&&c.object.type==='Identifier'&&c.object.name==='Math')category='shadowed_Math_call';
   else if(c.type==='MemberExpression'&&name&&arrayNames.has(name))category='array_named_call.'+name;
   else if(c.type==='MemberExpression')category=c.computed?'dynamic_member_call':'other_named_member_call';
   else if(c.type==='Identifier'&&refs.get(c)?.resolved)category='resolved_local_call';
   else if(c.type==='Identifier')category='unresolved_global_call';
   else category='other_callable_expression';
   calls.push(category);inc(category);
   if(name&&mutatingNames.has(name))inc('potential_mutating_method_call');
   if(name&&['call','apply','bind','toString','valueOf'].includes(name))inc('reflection_or_indirect_call');
  }
  if(n.type==='AssignmentExpression'||n.type==='UpdateExpression'||n.type==='UnaryExpression'&&n.operator==='delete'){
   const target=n.left||n.argument;
   if(target?.type==='MemberExpression'){inc('member_write');let root=target;while(root.type==='MemberExpression')root=root.object;if(global(root,'Math'))inc('global_Math_member_write');}
   else if(target?.type==='Identifier'&&refs.has(target)&&!refs.get(target).resolved)inc('unresolved_global_write');
  }
  if(n.type==='MemberExpression'&&['prototype','__proto__','constructor'].includes(property(n)))inc('prototype_or_constructor_access');
 }
 let otherGlobals=0,mathEscapes=0;
 for(const [n,r]of refs){
  if(r.resolved)continue;
  if(n.name==='Math'){
   const p=parents.get(n),g=parents.get(p);if(!(p?.type==='MemberExpression'&&p.object===n&&numericMath.has(property(p))&&g?.type==='CallExpression'&&g.callee===p))mathEscapes++;
  }else otherGlobals++;
 }
 inc('sources');if(otherGlobals)count.other_unresolved_global_references=otherGlobals;if(mathEscapes)count.Math_reference_outside_direct_numeric_call=mathEscapes;
 const onlyMath=calls.length>0&&calls.every(x=>x.startsWith('direct_numeric_Math.'))&&!otherGlobals&&!mathEscapes&&!count.prototype_or_constructor_access&&!count.unresolved_global_write;
 // This is syntactic investigation scope ONLY: argument numeric type, exceptional
 // values, alias/effects and finite original domain remain independently unproved.
 return {counts:count,call_count:calls.length,direct_numeric_Math_only_investigation_candidate:onlyMath,admitted:false};
}
export function controls(){
 const fixtures=[
 ['direct','function solve(a){return Math.abs(a);}',true],
 ['minmax','function solve(a,b){return Math.max(a,Math.min(a,b));}',true],
 ['shadow','function solve(Math){return Math.abs(1);}',false],
 ['write','function solve(a){Math.abs=a;return Math.abs(a);}',false],
 ['escape','function solve(a){var m=Math;return Math.abs(a);}',false],
 ['methodescape','function solve(a){var m=Math.abs;return Math.abs(a);}',false],
 ['dynamic','function solve(a){return Math[a](1);}',false],
 ['random','function solve(a){return Math.random();}',false],
 ['array','function solve(a){return a.pop();}',false],
 ['indirect','function solve(a){return Math.abs.call(null,a);}',false],
 ['local','function solve(a){return a(1);}',false],
 ['globalwrite','function solve(a){x=a;return Math.abs(a);}',false],
 ['prototype','function solve(a){a.__proto__=a;return Math.abs(1);}',false],
 ['no_calls','function solve(a){return a+1;}',false]
 ];return fixtures.map(([name,source,expected])=>({name,expected,observed:classify(source).direct_numeric_Math_only_investigation_candidate}));
}
