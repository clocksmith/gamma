// Linked research owner: parser-only, submitted sources are NEVER evaluated.
// Existing exact upstream parser loader and capture graph are copied unchanged.
import crypto from 'node:crypto';
import {acorn,scope} from './parser.mjs';
import {canonicalize} from './canonicalize.mjs';
const parse=text=>acorn.parse(text,{ecmaVersion:2022,ranges:true});
function inventory(ast){
 const paths=new Map(),nodes=[];
 function visit(node,path){
  if(!node||typeof node!=='object')return;
  if(typeof node.type==='string'){paths.set(node,path);nodes.push(node);}
  for(const key of Object.keys(node).sort()){
   if(['start','end','range','loc','raw'].includes(key))continue;
   const v=node[key];
   if(Array.isArray(v))v.forEach((x,i)=>visit(x,`${path}.${key}[${i}]`));
   else if(v&&typeof v==='object')visit(v,`${path}.${key}`);
  }
 }
 visit(ast,'$');return {paths,nodes};
}
export function resolution(source){
 const ast=parse(source),{paths}=inventory(ast);
 const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});
 const variables=[...new Set(manager.scopes.flatMap(s=>s.variables))],ids=new Map(variables.map((v,i)=>[v,i]));
 const occurrences=[];
 for(const v of variables){
  for(const node of v.identifiers)occurrences.push({path:paths.get(node),kind:'declaration',binding:ids.get(v)});
 }
 for(const s of manager.scopes)for(const ref of s.references){
  const row={path:paths.get(ref.identifier),kind:'reference',scope:manager.scopes.indexOf(ref.from),read:ref.isRead(),write:ref.isWrite(),init:!!ref.init};
  if(ref.resolved){if(!ids.has(ref.resolved))throw Error('unindexed binding');row.binding=ids.get(ref.resolved);}
  else row.unresolved_global=ref.identifier.name;
  occurrences.push(row);
 }
 if(occurrences.some(x=>typeof x.path!=='string'))throw Error('missing stable occurrence path');
 occurrences.sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b)));
 return {scopes:manager.scopes.map(s=>({type:s.type,upper:s.upper?manager.scopes.indexOf(s.upper):null,block:paths.get(s.block)})),bindings:variables.map(v=>({scope:manager.scopes.indexOf(v.scope),definitions:v.defs.map(d=>({type:d.type,name_path:paths.get(d.name),node_path:paths.get(d.node)}))})),occurrences};
}
export function compareResolution(before,after){
 if(JSON.stringify(resolution(before))!==JSON.stringify(resolution(after)))throw Error('occurrence-to-binding or unresolved-global mapping changed');
 return true;
}
export function strictSubset(source){
 const ast=parse(source),{nodes}=inventory(ast),reasons=new Set();
 // Deliberately narrow first admission: numeric/boolean scalar arithmetic,
 // local control flow and numeric indexing over separately audited JSON arrays.
 // No claims of a general reflection detector or arbitrary-domain equivalence.
 const denied=new Set(['CallExpression','NewExpression','TaggedTemplateExpression','TemplateLiteral','WithStatement','ImportExpression','ImportDeclaration','ExportNamedDeclaration','ExportDefaultDeclaration','ExportAllDeclaration','MetaProperty','ThisExpression','Super','ClassDeclaration','ClassExpression','FunctionExpression','ArrowFunctionExpression','AwaitExpression','YieldExpression','SpreadElement','RestElement']);
 for(const n of nodes){
  if(denied.has(n.type))reasons.add('unsupported_'+n.type);
  if(n.type==='Literal'&&(typeof n.value==='string'||n.regex))reasons.add('string_or_regex_value');
  if(n.type==='Property'&&(n.kind!=='init'||n.method||n.computed||n.shorthand))reasons.add('dynamic_or_ambiguous_property');
  if(n.type==='Identifier'&&['eval','Function','Reflect','Object','String','Proxy','Symbol','globalThis','require','process','arguments'].includes(n.name))reasons.add('reflection_or_ambient_identifier');
  if(n.type==='MemberExpression'){
   if(!n.computed&&n.property.name!=='length')reasons.add('non_length_named_property');
   if(n.computed&&!(n.property.type==='Identifier'||n.property.type==='Literal'&&Number.isInteger(n.property.value)&&n.property.value>=0))reasons.add('non_simple_numeric_index');
  }
 }
 const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});
 for(const s of manager.scopes)for(const ref of s.references){
  if(!ref.resolved)reasons.add('unresolved_global_reference');
  else if(ref.resolved.defs.some(d=>['FunctionName','ClassName'].includes(d.type)))reasons.add('observable_function_value');
 }
 return {admitted:reasons.size===0,reasons:[...reasons].sort(),required_external_audit:'exact source hash; JSON numeric/boolean/null arrays only; computed index bindings proven numeric; no callable/proxy/accessor inputs; source-specific no-reflection audit. This static result alone is NOT admission.'};
}
export function align(source,{audit,sourceSha256,mode='role'}={}){
 if(crypto.createHash('sha256').update(source,'utf8').digest('hex')!==sourceSha256)throw Error('actual source hash mismatch');
 if(!audit||audit.source_sha256!==sourceSha256||!/^[0-9a-f]{64}$/.test(sourceSha256||'')||audit.independent_review!==true||audit.numeric_json_domain!==true||audit.numeric_index_bindings!==true||audit.no_reflection_review!==true)throw Error('exact-source independent admission audit required');
 const admitted=strictSubset(source);if(!admitted.admitted)throw Error('unsupported subset: '+admitted.reasons.join(','));
 const transformed=canonicalize(source,mode);compareResolution(source,transformed.source);
 return {...transformed,occurrence_resolution_verified:true,source_sha256:sourceSha256,qualification:false};
}
