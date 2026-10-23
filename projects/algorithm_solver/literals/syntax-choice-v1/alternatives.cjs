// Guarded local source spellings; no source execution. JSON-lines worker protocol.
const acorn=require('/usr/share/nodejs/acorn');
const scopes=require('/usr/share/nodejs/eslint-scope');
const {bindings}=require('../binding-descent-v1/bindings.cjs');
function walk(n,visit,parent=null,key=null){visit(n,parent,key);for(const [k,v] of Object.entries(n)){
 if(Array.isArray(v)){for(const child of v)if(child&&typeof child.type==='string')walk(child,visit,n,k);}
 else if(v&&typeof v.type==='string')walk(v,visit,n,k);
}}
function bodyStrings(text,ast){
 const out=[text];
 for(const node of ast.body){
  const fs=[];
  if(node.type==='FunctionDeclaration'&&node.id?.name==='solve')fs.push(node);
  if(node.type==='VariableDeclaration')for(const d of node.declarations)if(d.id.name==='solve'&&['FunctionExpression','ArrowFunctionExpression'].includes(d.init?.type))fs.push(d.init);
  for(const f of fs){out.push(text.slice(f.start,f.end),text.slice(f.body.start,f.body.end));
   if(f.body.type==='BlockStatement')out.push(text.slice(f.body.start+1,f.body.end-1).trim());}
 }
 if(out.length===1)throw Error('missing solve entry');return out;
}
function alternatives(text,vocab,mode='combined',limit=256){
 const record=bindings(text);
 if(record.unsafe||!/^[\x00-\x7f]*$/.test(text))return {proposals:[],unsupported:true,reason:record.reason||'non_ascii',truncated:false};
 const ast=acorn.parse(text,{ecmaVersion:2022,ranges:true});const parents=new Map(),nodes=[];
 walk(ast,(n,p,k)=>{nodes.push(n);parents.set(n,{p,k});});
 const manager=scopes.analyze(ast,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});
 const refs=new Map();for(const s of manager.scopes)for(const ref of s.references)if(ref.resolved&&ref.resolved.scope.type!=='global')refs.set(ref.identifier.start,ref.resolved);
 // Source text is observable through implicit function coercion too. Only edit
 // within named bindings used solely as direct callees, or direct IIFEs.
 const allRefs=manager.scopes.flatMap(s=>s.references),allVars=[...new Set(manager.scopes.flatMap(s=>s.variables))];
 const functionNodes=new Set(['FunctionDeclaration','FunctionExpression','ArrowFunctionExpression']);
 let indirectReflection=false;
 for(const n of nodes){
  if(n.type==='ThisExpression'||n.type==='Identifier'&&['arguments','globalThis','window','global','self'].includes(n.name))indirectReflection=true;
  if(n.type==='MemberExpression'){
   const key=n.computed?n.property.type==='Literal'?n.property.value:null:n.property.name;
   if(['constructor','callee','caller','eval','Function'].includes(key))indirectReflection=true;
  }
 }
 if(indirectReflection)return {proposals:[],unsupported:true,reason:'indirect_reflection_guard',truncated:false};
 const safeFunctions=new Map();
 for(const fn of nodes.filter(n=>functionNodes.has(n.type))){
  const {p,k}=parents.get(fn)||{};const ids=[];if(fn.id)ids.push(fn.id);
  if(p?.type==='VariableDeclarator'&&k==='init'&&p.id.type==='Identifier')ids.push(p.id);
  if(!ids.length){safeFunctions.set(fn,p?.type==='CallExpression'&&k==='callee');continue;}
  const vars=allVars.filter(v=>v.identifiers.some(i=>ids.some(id=>id.start===i.start)));
  const names=new Set(ids.map(i=>i.name));
  const uses=allRefs.filter(r=>vars.includes(r.resolved)||!r.resolved&&names.has(r.identifier.name));
  safeFunctions.set(fn,vars.length>0&&uses.every(r=>{
   const parent=parents.get(r.identifier);return parent?.p.type==='CallExpression'&&parent.k==='callee';
  }));
 }
 function safeContainer(node){
  for(let current=node;current;current=parents.get(current)?.p)if(functionNodes.has(current.type)&&!safeFunctions.get(current))return false;
  return true;
 }

 const word=n=>text.slice(n.start,n.end),has=n=>n?.type==='Identifier'&&refs.has(n.start);
 const equal=(a,b)=>has(a)&&has(b)&&refs.get(a.start)===refs.get(b.start);
 const arithmetic=new Set(['+','-','*','/','%','**','<<','>>','>>>','&','|','^']);
 function discarded(n){
  const {p,k}=parents.get(n)||{};if(!p)return false;
  if(p.type==='ExpressionStatement'&&k==='expression')return true;
  if(p.type==='ForStatement'&&['init','update'].includes(k))return true;
  if(p.type==='SequenceExpression')return p.expressions.at(-1)!==n||discarded(p);
  if(p.type==='UnaryExpression'&&p.operator==='void')return true;
  return false;
 }
 const specs=[];
 function offer(node,replacement,kind){if(safeContainer(node)&&word(node)!==replacement)specs.push({start:node.start,end:node.end,replacement,kind});}
 function negate(n){return n.type==='UnaryExpression'&&n.operator==='!'?'('+word(n.argument)+')':'!('+word(n)+')';}
 for(const n of nodes){
  if(mode!=='flow'){
   if(n.type==='AssignmentExpression'&&has(n.left)){
    if(n.operator.endsWith('=')&&arithmetic.has(n.operator.slice(0,-1)))
     offer(n,word(n.left)+'='+word(n.left)+n.operator.slice(0,-1)+'('+word(n.right)+')','expand_compound');
    if(n.operator==='='&&n.right.type==='BinaryExpression'&&arithmetic.has(n.right.operator)&&equal(n.left,n.right.left))
     offer(n,word(n.left)+n.right.operator+'=('+word(n.right.right)+')','contract_compound');
   }
   if(n.type==='UpdateExpression'&&has(n.argument)&&discarded(n))
    offer(n,n.prefix?word(n.argument)+n.operator:n.operator+word(n.argument),'discarded_update');
  }
  if(mode!=='arithmetic'){
   if(n.type==='IfStatement'&&n.alternate&&n.consequent.type==='BlockStatement'&&n.alternate.type==='BlockStatement')
    offer(n,'if('+negate(n.test)+')'+word(n.alternate)+'else'+word(n.consequent),'invert_if');
   if(n.type==='ConditionalExpression')offer(n,'('+negate(n.test)+'?('+word(n.alternate)+'):('+word(n.consequent)+'))','invert_conditional');
   if(n.type==='WhileStatement')offer(n,'for(;'+word(n.test)+';)'+word(n.body),'while_to_for');
   if(n.type==='ForStatement'&&!n.init&&!n.update)offer(n,'while('+ (n.test?word(n.test):'true') +')'+word(n.body),'for_to_while');
  }
 }
 const cmp=(a,b)=>a<b?-1:a>b?1:0;
 specs.sort((a,b)=>a.start-b.start||a.end-b.end||cmp(a.kind,b.kind)||cmp(a.replacement,b.replacement));
 const seen=new Set(),proposals=[],dictionary=new Set(vocab);let truncated=false;
 for(const spec of specs){
  if(proposals.length>=limit){truncated=true;break;}
  const candidate=text.slice(0,spec.start)+spec.replacement+text.slice(spec.end);
  if(seen.has(candidate))continue;seen.add(candidate);
  let parsed;try{parsed=acorn.parse(candidate,{ecmaVersion:2022});}catch{continue;}
  if(bodyStrings(candidate,parsed).some(x=>dictionary.has(x)))continue;
  proposals.push({text:candidate,kind:spec.kind,start:spec.start,end:spec.end});
 }
 return {proposals,unsupported:false,truncated};
}
if(require.main===module){
 const rl=require('node:readline').createInterface({input:process.stdin});
 rl.on('line',line=>{try{const a=JSON.parse(line);process.stdout.write(JSON.stringify(alternatives(a.text,a.vocab,a.mode,a.limit))+'\n');}
 catch(e){process.stdout.write(JSON.stringify({error:String(e)})+'\n');}});
}
module.exports={alternatives};
