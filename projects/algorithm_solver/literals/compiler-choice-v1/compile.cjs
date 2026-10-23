// Fixed compiler profile family. Source is parsed/transformed, never executed here.
const fs=require('node:fs'),terser=require('/usr/share/nodejs/terser'),acorn=require('/usr/share/nodejs/acorn');
const safety={unsafe:false,unsafe_arrows:false,unsafe_comps:false,unsafe_Function:false,unsafe_math:false,
 unsafe_symbols:false,unsafe_methods:false,unsafe_proto:false,unsafe_regexp:false,unsafe_undefined:false,
 pure_getters:false,pure_funcs:null,pure_new:false,drop_console:false,drop_debugger:false,
 keep_fargs:true,keep_fnames:true,keep_classnames:true,keep_infinity:true,toplevel:false,module:false};
const profiles={layout:false,
 syntax:{defaults:false,booleans:true,conditionals:true,if_return:true,join_vars:true,sequences:true,passes:1,...safety},
 standard:{defaults:true,passes:2,...safety}};
function reflection(text){
 const ast=acorn.parse(text,{ecmaVersion:2022});let found=false;
 function visit(n){
  if(n.type==='WithStatement'||(n.type==='Identifier'&&['eval','Function'].includes(n.name))||
     (n.type==='MemberExpression'&&(!n.computed&&['name','toString'].includes(n.property.name)||n.computed&&n.property.type==='Literal'&&['name','toString'].includes(n.property.value))))found=true;
  for(const v of Object.values(n))if(Array.isArray(v)){for(const c of v)if(c&&typeof c.type==='string')visit(c);}
  else if(v&&typeof v.type==='string')visit(v);
 }visit(ast);return found;
}
async function compile(text){
 const candidates={original:text},errors={};
 if(reflection(text))return {candidates,errors,skip:'reflection_guard'};
 for(const [name,compress] of Object.entries(profiles)){
  try{
   const result=await terser.minify(text,{ecma:2022,module:false,toplevel:false,mangle:false,keep_fnames:true,keep_classnames:true,
     compress,format:{comments:false,ascii_only:true,semicolons:true}});
   const code=result.code;
   if(!code||Buffer.byteLength(code)>2*Buffer.byteLength(text))throw Error('empty or expansion cap');
   acorn.parse(code,{ecmaVersion:2022});candidates[name]=code;
  }catch(e){errors[name]=String(e.message);}
 }
 return {candidates,errors,skip:null};
}
if(require.main===module)(async()=>{const input=JSON.parse(fs.readFileSync(0,'utf8')),out={};for(const [id,text] of Object.entries(input))out[id]=await compile(text);process.stdout.write(JSON.stringify(out));})().catch(e=>{console.error(e);process.exitCode=1;});
module.exports={compile,profiles};
