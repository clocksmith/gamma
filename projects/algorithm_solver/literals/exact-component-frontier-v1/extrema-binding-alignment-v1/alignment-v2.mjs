// Linked restricted feature owner: parse/rename strings only, never execute sources.
import crypto from 'node:crypto';
import {acorn,scope} from '../ast-binding-alignment-v1/parser.mjs';
import {strictSubset,compareResolution} from '../ast-binding-alignment-v1/alignment.mjs';
import {numericIndexProof} from '../ast-binding-alignment-v1/numeric-index-proof-v2.mjs';
import {canonicalize} from '../ast-binding-alignment-v1/canonicalize.mjs';
export function extremaSubset(source){
 const ast=acorn.parse(source,{ecmaVersion:2022,ranges:true}),nodes=[],parents=new Map();
 function walk(n,p){if(!n?.type)return;nodes.push(n);parents.set(n,p);for(const v of Object.values(n)){if(Array.isArray(v)){for(const c of v)if(c?.type)walk(c,n);}else if(v?.type)walk(v,n);}}walk(ast,null);
 const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false}),refs=new Map();for(const s of manager.scopes)for(const r of s.references)refs.set(r.identifier,r);
 const reasons=new Set(strictSubset(source).reasons.filter(x=>!['unsupported_CallExpression','non_length_named_property','unresolved_global_reference'].includes(x)));
 const math=n=>n?.type==='Identifier'&&n.name==='Math'&&refs.has(n)&&!refs.get(n).resolved;
 const callee=n=>n?.type==='MemberExpression'&&!n.computed&&math(n.object)&&['min','max'].includes(n.property.name);
 const directMember=n=>callee(n)&&parents.get(n)?.type==='CallExpression'&&parents.get(n).callee===n;
 for(const s of manager.scopes)for(const v of s.variables)if(v.name==='Math')reasons.add('shadowed_Math_binding');
 for(const [n,r]of refs)if(!r.resolved&&!(math(n)&&directMember(parents.get(n))&&parents.get(n).object===n))reasons.add('unresolved_or_escaped_global');
 function numericShape(n){
  if(n?.type==='Literal')return typeof n.value==='number'&&Number.isFinite(n.value);
  if(n?.type==='Identifier')return !!refs.get(n)?.resolved; // type must be independently audited
  if(n?.type==='MemberExpression')return memberShape(n);
  if(n?.type==='UnaryExpression')return ['+','-','~'].includes(n.operator)&&numericShape(n.argument);
  if(n?.type==='BinaryExpression')return ['+','-','*','/','%','**','<<','>>','>>>','&','|','^'].includes(n.operator)&&numericShape(n.left)&&numericShape(n.right);
  if(n?.type==='ConditionalExpression')return conditionShape(n.test)&&numericShape(n.consequent)&&numericShape(n.alternate);
  if(n?.type==='CallExpression')return callee(n.callee)&&n.arguments.length>=1&&n.arguments.every(numericShape);
  return false;
 }
 // Full recursive purity check: no unchecked conditional test, receiver or index.
 // This proves only an allowed nonmutating syntax shape, not dynamic Number type.
 function receiverShape(n){
  if(n?.type==='Identifier')return !!refs.get(n)?.resolved;
  return n?.type==='MemberExpression'&&memberShape(n);
 }
 function memberShape(n){
  return !n.optional&&!callee(n)&&receiverShape(n.object)&&(n.computed?numericShape(n.property):n.property.name==='length');
 }
 function conditionShape(n){
  if(n?.type==='Literal'&&typeof n.value==='boolean')return true;
  if(n?.type==='UnaryExpression'&&n.operator==='!')return conditionShape(n.argument);
  if(n?.type==='BinaryExpression'&&['<','<=','>','>=','===','!==','==','!='].includes(n.operator))return numericShape(n.left)&&numericShape(n.right);
  if(n?.type==='LogicalExpression'&&['&&','||'].includes(n.operator))return conditionShape(n.left)&&conditionShape(n.right);
  if(n?.type==='ConditionalExpression')return conditionShape(n.test)&&conditionShape(n.consequent)&&conditionShape(n.alternate);
  return numericShape(n);
 }
 let calls=0;
 for(const n of nodes){
  if(n.type==='CallExpression'){
   calls++;if(!callee(n.callee)||n.optional||n.arguments.length<1||!n.arguments.every(numericShape))reasons.add('unsupported_callee_or_argument_shape');
  }
  if(n.type==='MemberExpression'&&!n.computed&&n.property.name!=='length'&&!directMember(n))reasons.add('unsupported_member');
  if(n.type==='AssignmentExpression'||n.type==='UpdateExpression'||n.type==='UnaryExpression'&&n.operator==='delete'){
   const target=n.left||n.argument;if(target?.type==='MemberExpression'||target?.type==='ArrayPattern'||target?.type==='ObjectPattern')reasons.add('member_or_destructuring_write');
  }
 }
 if(!calls)reasons.add('no_extrema_feature');
 const index=numericIndexProof(source);if(!index.all_computed_indices_inductively_numeric)reasons.add('unproved_computed_index');
 return {syntactic_candidate:reasons.size===0,reasons:[...reasons].sort(),extrema_calls:calls,admitted:false,required_external_proof:'Exact-source finite original contract: all extrema arguments are primitive Numbers, numeric array access/index bounds and all writes justified, no object coercion/accessors/proxies/callbacks, no reflection; pinned fresh runtime with original unmodified Math.min/max. Syntactic candidate is not admission.'};
}
export function alignExtrema(source,{sourceSha256,audit,mode='role'}={}){
 if(crypto.createHash('sha256').update(source).digest('hex')!==sourceSha256)throw Error('exact source hash');
 if(!audit||audit.source_sha256!==sourceSha256||!['cases_sha256','effects_sha256','runtime_sha256'].every(k=>/^[0-9a-f]{64}$/.test(audit[k]||''))||!['independent_review','finite_contract_numeric_arguments','numeric_index_and_array_access_review','no_reflection_or_coercion','fresh_unmodified_intrinsics'].every(k=>audit[k]===true))throw Error('independent finite source/domain/runtime audit required');
 const subset=extremaSubset(source);if(!subset.syntactic_candidate)throw Error('unsupported extrema subset: '+subset.reasons.join(','));
 if(!['format','role'].includes(mode))throw Error('matched format/role modes only');
 const transformed=canonicalize(source,mode);compareResolution(source,transformed.source);
 return {...transformed,occurrence_resolution_verified:true,source_sha256:sourceSha256,qualification:false,finite_contract_only:true};
}
