// Scope-aware local naming with a fixed, small alphabet family; no compression or property mangling.
const fs=require('node:fs'),terser=require('/usr/share/nodejs/terser'),acorn=require('/usr/share/nodejs/acorn'),scope=require('/usr/share/nodejs/eslint-scope');
const alphabet='abcdefghijklmnopqrstuvwxyz';
const orders=Object.fromEntries([0,4,8,13,17,18,19,23].map(n=>['rotate'+String(n).padStart(2,'0'),alphabet.slice(n)+alphabet.slice(0,n)]));
orders.reverse=[...alphabet].reverse().join('');
function nth(chars){return {get(n){let s='';do{s=chars[n%26]+s;n=Math.floor(n/26)-1;}while(n>=0);return s;}};}
function ast(text){return acorn.parse(text,{ecmaVersion:2022,ranges:true});}
function reflection(root){
 let found=false;
 function walk(n){
  if(n.type==='WithStatement'||n.type==='Identifier'&&['eval','Function'].includes(n.name)||n.type==='MemberExpression'&&
   (!n.computed&&['name','toString'].includes(n.property.name)||n.computed&&n.property.type==='Literal'&&['name','toString'].includes(n.property.value)))found=true;
  for(const v of Object.values(n))if(Array.isArray(v)){for(const c of v)if(c&&typeof c.type==='string')walk(c);}else if(v&&typeof v.type==='string')walk(v);
 }walk(root);return found;
}
function stats(root){
 const manager=scope.analyze(root,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});
 const variables=manager.scopes.flatMap(s=>s.type==='global'?[]:s.variables.filter(v=>v.defs.length));
 return {bindings:variables.length,distinct_spellings:new Set(variables.map(v=>v.name)).size};
}
async function compile(text){
 const root=ast(text),candidates={original:text},errors={},binding_stats={};
 try{binding_stats.original=stats(root);}catch(e){errors.scope_analysis=String(e.message);binding_stats.original=null;return {candidates,errors,binding_stats,skip:'scope_analysis_failed'};}
 if(reflection(root))return {candidates,errors,binding_stats,skip:'reflection_guard'};
 for(const name of ['layout','default',...Object.keys(orders)]){
  try{
   const mangle=name==='layout'?false:{toplevel:false,module:false,eval:false,keep_fnames:true,keep_classnames:true,reserved:['solve'],
      ...(orders[name]?{nth_identifier:nth(orders[name])}:{})};
   const result=await terser.minify(text,{ecma:2022,module:false,toplevel:false,compress:false,mangle,keep_fnames:true,keep_classnames:true,
      format:{comments:false,ascii_only:true,semicolons:true}});
   const code=result.code;if(!code||Buffer.byteLength(code)>2*Buffer.byteLength(text))throw Error('empty or expansion cap');
   binding_stats[name]=stats(ast(code));candidates[name]=code;
  }catch(e){errors[name]=String(e.message);}
 }
 return {candidates,errors,binding_stats,skip:null};
}
if(require.main===module)(async()=>{const input=JSON.parse(fs.readFileSync(0,'utf8')),out={};for(const [id,text] of Object.entries(input))out[id]=await compile(text);process.stdout.write(JSON.stringify(out));})().catch(e=>{console.error(e);process.exitCode=1;});
module.exports={compile,nth,orders};
