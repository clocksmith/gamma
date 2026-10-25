// Conservative inductive numeric-index witnesses; parser-only, no source execution.
import {acorn,scope} from './parser.mjs';
export function numericIndexProof(source){
 const ast=acorn.parse(source,{ecmaVersion:2022,ranges:true}),parents=new Map(),paths=new Map(),nodes=[];
 function walk(n,path,parent){if(!n||typeof n!=='object'||typeof n.type!=='string')return;nodes.push(n);paths.set(n,path);parents.set(n,parent);for(const key of Object.keys(n).sort()){const v=n[key];if(Array.isArray(v))v.forEach((x,i)=>walk(x,`${path}.${key}[${i}]`,n));else walk(v,`${path}.${key}`,n);}}
 walk(ast,'$',null);
 const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});
 const variables=[...new Set(manager.scopes.flatMap(s=>s.variables))],ids=new Map(variables.map((v,i)=>[v,i])),resolved=new Map();
 for(const s of manager.scopes)for(const r of s.references)resolved.set(r.identifier,r.resolved);
 const number=n=>n?.type==='Literal'&&typeof n.value==='number'&&Number.isFinite(n.value);
 let candidates=new Set(variables.filter(v=>v.defs.length===1&&v.defs[0].type==='Variable'&&number(v.defs[0].node.init)));
 function numeric(n,known){
  if(number(n))return true;
  if(n?.type==='Identifier')return known.has(resolved.get(n));
  if(n?.type==='UnaryExpression'&&['+','-','~'].includes(n.operator))return numeric(n.argument,known);
  if(n?.type==='BinaryExpression'&&['+','-','*','/','%','**','<<','>>','>>>','&','|','^'].includes(n.operator))return numeric(n.left,known)&&numeric(n.right,known);
  return false;
 }
 function preserved(v,known){
  const init=v.defs[0].node.init;
  for(const r of v.references){
   if(r.init&&r.writeExpr===init)continue;
   // Reject potential pre-initialization use, including earlier textual closures.
   if(r.identifier.start<=init.end)return false;
   if(!r.isWrite())continue;
   const p=parents.get(r.identifier);
   if(p?.type==='UpdateExpression'&&['++','--'].includes(p.operator))continue;
   if(p?.type==='AssignmentExpression'&&p.left===r.identifier&&['=','+=','-=','*=','/=','%=','**=','<<=','>>=','>>>=','&=','|=','^='].includes(p.operator)&&numeric(p.right,known))continue;
   return false;
  }
  return true;
 }
 let changed=true;
 while(changed){changed=false;for(const v of [...candidates])if(!preserved(v,candidates)){candidates.delete(v);changed=true;}}
 const indices=nodes.filter(n=>n.type==='MemberExpression'&&n.computed).map(n=>({path:paths.get(n.property),kind:n.property.type,binding_id:n.property.type==='Identifier'&&resolved.get(n.property)?ids.get(resolved.get(n.property)):null,proven_numeric:number(n.property)||n.property.type==='Identifier'&&candidates.has(resolved.get(n.property))}));
 return {all_computed_indices_inductively_numeric:indices.every(x=>x.proven_numeric),indices,numeric_binding_ids:[...candidates].map(v=>ids.get(v)).sort((a,b)=>a-b),proof_rule:'Single numeric-literal declaration, no textual preinit use, every later write preserves number over simultaneous inductive numeric bindings; parameter indices/unknown writes rejected. Does not establish source input domain or algorithm correctness.'};
}
