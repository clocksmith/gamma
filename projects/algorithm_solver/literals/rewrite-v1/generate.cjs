"use strict";
// All transformations are offline; decoding still concatenates exact strings.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const acorn=require('acorn'),scope=require('eslint-scope'),printer=require('escodegen');
const arrow=require('../pass3/generate.cjs').arrow;
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const parse=s=>acorn.parse(s,{ecmaVersion:2022,ranges:true});
function walk(n,fn,p=null,k=null,at=''){
 if(!n||typeof n.type!=='string')return;fn(n,p,k,at);
 for(const [key,value] of Object.entries(n)){
  if(Array.isArray(value))value.forEach((v,i)=>walk(v,fn,n,key,at+'.'+key+'['+i+']'));
  else if(value&&typeof value.type==='string')walk(value,fn,n,key,at+'.'+key);
 }
}
function analyze(tree){
 const manager=scope.analyze(tree,{ecmaVersion:2022,sourceType:'script',optimistic:true});
 const paths=new Map(),parents=new Map();walk(tree,(n,p,k,at)=>{paths.set(n,at);parents.set(n,{p,k});});
 const variables=manager.scopes.flatMap(s=>s.variables).filter(v=>v.defs.length&&v.identifiers.length&&v.name!=='arguments');
 const roots=new Map(variables.map(v=>[v,v])),nodes=new Map();
 function root(v){if(roots.get(v)!==v)roots.set(v,root(roots.get(v)));return roots.get(v);}
 for(const v of variables)for(const n of v.identifiers){if(nodes.has(n))roots.set(root(v),root(nodes.get(n)));else nodes.set(n,v);}
 const groups=new Map(),of=new Map();
 for(const v of variables){const r=root(v);if(!groups.has(r))groups.set(r,{vars:[],ids:new Set(),neighbors:new Set()});const g=groups.get(r);g.vars.push(v);v.identifiers.forEach(n=>g.ids.add(n));of.set(v,g);}
 const refs=[];
 for(const sc of manager.scopes)for(const r of sc.references){
  const g=of.get(r.resolved);refs.push([paths.get(r.identifier),g?[...g.ids].map(n=>paths.get(n)).sort():'free:'+r.identifier.name]);
 }
 return {manager,paths,parents,groups:[...groups.values()],of,refs:refs.sort((a,b)=>a[0].localeCompare(b[0]))};
}
function graph(source){return analyze(parse(source)).refs;}
function rename(source,mode='scope'){
 const tree=parse(source),data=analyze(tree),{manager,groups,of,parents}=data;
 walk(tree,n=>{if(n.type==='WithStatement'||n.type==='Identifier'&&['eval','Function'].includes(n.name))throw Error('reflective scope unsupported');});
 const forbidden=new Set(['arguments','solve',...manager.globalScope.through.map(r=>r.identifier.name)]);
 const edge=(a,b)=>{if(a&&b&&a!==b){a.neighbors.add(b);b.neighbors.add(a);}};
 for(const sc of manager.scopes){const gs=sc.variables.map(v=>of.get(v)).filter(Boolean);for(const a of gs)for(const b of gs)edge(a,b);}
 // A renamed inner declaration must not capture a reference to an outer one.
 for(const sc of manager.scopes)for(const ref of sc.references){
  const target=of.get(ref.resolved);if(!target)continue;
  for(let s=ref.from;s;s=s.upper){for(const v of s.variables)edge(target,of.get(v));if(s===ref.resolved.scope)break;}
 }
 const alphabet=Array.from({length:26},(_,i)=>String.fromCharCode(97+i));
 function preference(g){
  const vars=g.vars,def=vars[0].defs[0];
  if(vars.some(v=>v.scope.type==='global'&&v.defs.some(d=>d.type==='FunctionName')))return ['h'];
  if(vars.some(v=>v.defs.some(d=>d.type==='ClassName')))return ['H'];
  if(def.type==='Parameter')return [];
  if(mode!=='role')return [];
  const init=def.node?.init,decl=parents.get(def.node)?.p,owner=parents.get(decl)?.p;
  if(owner?.type==='ForStatement')return ['i','j'];
  if(owner?.type==='ForOfStatement')return ['x','y'];
  if(owner?.type==='ForInStatement')return ['k'];
  if(init?.type==='NewExpression'&&init.callee.type==='Identifier'){
   if(init.callee.name==='Map')return ['m'];if(init.callee.name==='Set')return ['s'];if(init.callee.name==='Array')return ['r'];
  }
  if(init?.type==='ArrayExpression')return ['r'];
  if(init?.type==='ObjectExpression')return ['m'];
  if(init?.type==='Literal'&&['number','boolean'].includes(typeof init.value))return ['r','n'];
  return [];
 }
 groups.sort((a,b)=>Math.min(...[...a.ids].map(n=>n.start))-Math.min(...[...b.ids].map(n=>n.start)));
 for(const g of groups){
  if(g.vars.some(v=>v.name==='solve')){g.name='solve';continue;}
  const unavailable=new Set([...forbidden,...[...g.neighbors].map(n=>n.name).filter(Boolean)]);
  const candidates=[...preference(g),...alphabet,...Array.from({length:256},(_,i)=>'v'+i)];
  g.name=candidates.find(n=>!unavailable.has(n));if(!g.name)throw Error('name budget');
 }
 const names=new Map();
 for(const g of groups)for(const v of g.vars){for(const n of v.identifiers)names.set(n,g.name);for(const r of v.references)names.set(r.identifier,g.name);}
 walk(tree,n=>{if(n.type==='Property'&&n.shorthand&&names.has(n.value)){n.key={...n.key};n.shorthand=false;}if(n.type==='Identifier'&&names.has(n))n.name=names.get(n);});
 const result=printer.generate(tree,{format:{compact:true,quotes:'single',escapeless:false,semicolons:true}})+'\n';
 if([...result].some(c=>c!=='\n'&&(c.charCodeAt(0)<32||c.charCodeAt(0)>126)))throw Error('non-ASCII output');
 if(JSON.stringify(data.refs)!==JSON.stringify(graph(result)))throw Error('binding graph changed');
 return result;
}
function fragments(source){
 const out=new Map(),tree=parse(source);let solve;
 walk(tree,n=>{if(n.type==='FunctionDeclaration'&&n.id?.name==='solve')solve=n;
  if(n.type==='VariableDeclarator'&&n.id?.name==='solve')solve=n.init;
 });
 const fullBody=solve?.body;
 walk(tree,(n,p,k)=>{
  if(n===tree||n===solve||n===fullBody)return;
  if(n.type==='Identifier'||n.type==='Literal')return;
  const text=source.slice(n.start,n.end);
  if(text.length>1&&Buffer.byteLength(text)<=512&&text!==source.trim())out.set(text,n.type);
 });
 return [...out].map(([text,type])=>({text,type}));
}
function main(root,out){
 const contract=JSON.parse(fs.readFileSync(path.join(root,'contract.json'))),base=path.dirname(root);
 for(const [relative,digest]of Object.entries(contract.inputs))if(sha(fs.readFileSync(path.join(root,relative)))!==digest)throw Error('input drift '+relative);
 fs.mkdirSync(out);fs.mkdirSync(path.join(out,'sources'));const rows=[],attempts=[],seen=new Set(),byProblem=new Map();
 const scale=JSON.parse(fs.readFileSync(path.join(base,'scale-v2/generated/manifest.json')));
 const originals=new Map(scale.rows.filter(r=>r.variant==='original').map(r=>[r.id,r]));
 for(const r of originals.values())rows.push({...r,file:path.join('..','..','scale-v2/generated',r.file)});
 for(const r of scale.rows)seen.add(r.id+':'+r.sha256);
 const parents=scale.rows.filter(r=>r.variant==='canonical').map(r=>({id:r.id,file:path.join('..','scale-v2/generated',r.file),sha256:r.sha256,origin:'scale',method:r.method}));
 // Only unchanged-baseline and pure shared-frequency-helper alternatives. Do not
 // import historical XOR-to-map or Array.from fold memory regressions.
 const legacy=JSON.parse(fs.readFileSync(path.join(base,'pass3/generated/manifest.json')));
 const legacyQ=JSON.parse(fs.readFileSync(path.join(base,'pass3/qualification-v1/report.json')));
 for(const [key,vs]of Object.entries(legacy.variants)){
  const id=Number(key);for(const name of ['baseline','shared']){
   const r=vs[name];if(!r||name==='shared'&&id===136)continue;
   const q=legacyQ.rows.find(x=>Number(x.problem)===id&&x.variant===name);
   if(!q?.passed||q.source_sha256!==r.sha256)throw Error('unqualified legacy source');
   parents.push({id,file:path.join('..','pass3/generated',r.file),sha256:r.sha256,origin:'legacy-'+name,method:originals.get(id).method});
  }
 }
 for(const parent of parents){
  const source=fs.readFileSync(path.join(root,parent.file),'utf8');if(sha(source)!==parent.sha256)throw Error('source drift');
  for(const mode of ['scope','role']){
   let normalized;
   try{normalized=rename(source,mode);}catch(e){attempts.push({parent,mode,status:'rejected',reason:e.message});continue;}
   const options=[[mode,normalized]];const a=arrow(normalized);if(a.status==='rewritten')options.push([mode+'-arrow',rename(a.source,mode)]);
   for(const [label,text]of options){
    const digest=sha(text),identity=parent.id+':'+digest;const attempt={parent,mode:label,sha256:digest,status:seen.has(identity)?'duplicate':'generated'};attempts.push(attempt);if(seen.has(identity))continue;
    seen.add(identity);const count=(byProblem.get(parent.id)||0)+1;byProblem.set(parent.id,count);
    const variant=parent.origin+'-'+label+'-'+count,file=`sources/${String(parent.id).padStart(4,'0')}-${variant}.js`;
    fs.writeFileSync(path.join(out,file),text);rows.push({id:parent.id,variant,file,sha256:digest,parent,entry:'solve',interface:'named-function',method:parent.method,transform:label});
   }
  }
 }
 if(rows.length-originals.size>contract.bounds.max_new_sources)throw Error('new-source budget');
 const pools={};for(const r of rows.filter(r=>r.variant!=='original'))pools[r.id+'/'+r.variant]=fragments(fs.readFileSync(path.join(out,r.file),'utf8'));
 const manifest={schema:'gamma.literal-rewrite-sources.v1',rows,attempts,source_count:rows.length,generator_sha256:sha(fs.readFileSync(__filename)),contract_sha256:sha(fs.readFileSync(path.join(root,'contract.json')))};
 fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(manifest,null,2)+'\n');fs.writeFileSync(path.join(out,'fragments.json'),JSON.stringify(pools)+'\n');
 console.log(JSON.stringify({sources:rows.length,attempts:attempts.length,rejected:attempts.filter(r=>r.status==='rejected').length}));
}
if(require.main===module)main(...process.argv.slice(2));module.exports={rename,graph,fragments};
