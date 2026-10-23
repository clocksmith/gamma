// Capture-conflict graph for exact-span local renaming. No source execution.
const fs=require('node:fs'),acorn=require('/usr/share/nodejs/acorn'),scope=require('/usr/share/nodejs/eslint-scope');
function walk(n,visit){visit(n);for(const v of Object.values(n))if(Array.isArray(v)){for(const c of v)if(c&&typeof c.type==='string')walk(c,visit);}else if(v&&typeof v.type==='string')walk(v,visit);}
function bindings(text){
 const ast=acorn.parse(text,{ecmaVersion:2022,ranges:true}),reservedSpans=new Set();let unsafe=false;
 const reserve=n=>walk(n,x=>{if(x.type==='Identifier')reservedSpans.add(x.start+':'+x.end)});
 walk(ast,n=>{
  if(n.type==='WithStatement'||n.type==='Identifier'&&['eval','Function'].includes(n.name)||n.type==='MemberExpression'&&
   (!n.computed&&['name','toString'].includes(n.property.name)||n.computed&&n.property.type==='Literal'&&['name','toString'].includes(n.property.value)))unsafe=true;
  if(n.type==='Property'&&n.shorthand){reserve(n.key);reserve(n.value);}
  if(['FunctionDeclaration','FunctionExpression','ClassDeclaration','ClassExpression'].includes(n.type)&&n.id)reserve(n.id);
  if(n.type==='VariableDeclarator'&&['FunctionExpression','ArrowFunctionExpression','ClassExpression'].includes(n.init?.type))reserve(n.id);
  if(['AssignmentPattern','AssignmentExpression'].includes(n.type)&&['FunctionExpression','ArrowFunctionExpression','ClassExpression'].includes(n.right?.type))reserve(n.left);
 });
 const manager=scope.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});
 const vars=[...new Set(manager.scopes.flatMap(s=>s.variables))],ids=new Map(vars.map((v,i)=>[v,i]));
 const neighbors=vars.map(()=>new Set()),forbidden=vars.map(()=>new Set());
 function edge(a,b){if(a!==b){neighbors[a].add(b);neighbors[b].add(a);}}
 for(const s of manager.scopes){
  const own=s.variables.map(v=>ids.get(v));
  for(let i=0;i<own.length;i++)for(let j=i+1;j<own.length;j++)edge(own[i],own[j]);
  for(const ref of s.references){
   const target=ref.resolved;
   if(target&&ids.has(target)){
    const id=ids.get(target);let cursor=ref.from;
    while(cursor){
     for(const other of cursor.variables)edge(id,ids.get(other));
     if(cursor===target.scope)break;cursor=cursor.upper;
    }
    if(!cursor)throw Error('resolved reference scope is not an ancestor');
   }else{
    for(let cursor=ref.from;cursor;cursor=cursor.upper)for(const v of cursor.variables)forbidden[ids.get(v)].add(ref.identifier.name);
   }
  }
 }
 const records=vars.map((v,id)=>{
  const nodes=[...v.identifiers,...v.references.map(r=>r.identifier)];
  const spans=[...new Map(nodes.map(n=>[n.start,[n.start,n.end]])).values()].sort((a,b)=>a[0]-b[0]);
  const eligible=!unsafe&&v.scope.type!=='global'&&v.scope.type!=='module'&&v.scope.type!=='class'&&v.defs.length>0&&
    v.defs.every(d=>['Parameter','Variable','CatchClause'].includes(d.type))&&v.identifiers.length>0&&
    nodes.every(n=>n.type==='Identifier'&&text.slice(n.start,n.end)===v.name&&!reservedSpans.has(n.start+':'+n.end));
  return {id,name:v.name,scope:manager.scopes.indexOf(v.scope),eligible,spans,neighbors:[...neighbors[id]].sort((a,b)=>a-b),forbidden:[...forbidden[id]].sort()};
 });
 // Shared AST declaration positions (e.g. class inner/outer names) never receive conflicting edits.
 const owners=new Map();for(const v of records)for(const [a,b] of v.spans){let key=a+':'+b;const set=owners.get(key)||new Set();set.add(v.id);owners.set(key,set);}
 for(const v of records)if(v.spans.some(([a,b])=>owners.get(a+':'+b).size>1))v.eligible=false;
 let reason=unsafe?'reflection_guard':null;
 for(const v of records)if(v.eligible&&(v.neighbors.some(i=>records[i].name===v.name)||v.forbidden.includes(v.name)))reason=reason||'original_graph_conflict';
 if(reason)for(const v of records)v.eligible=false;
 return {variables:records,unsafe:!!reason,reason};
}
if(require.main===module){const input=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(Object.fromEntries(Object.entries(input).map(([id,text])=>[id,bindings(text)]))));}
module.exports={bindings};
