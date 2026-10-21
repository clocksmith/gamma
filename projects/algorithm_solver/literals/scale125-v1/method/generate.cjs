const fs=require('fs'),path=require('path'),crypto=require('crypto');
const L='/home/x/deco/gamma/output/literal-joint-v1/projects/algorithm_solver/literals';
const old=require(L+'/scale-v2/generate.cjs'),rw=require(L+'/rewrite-v1/generate.cjs'),arrow=require(L+'/pass3/generate.cjs').arrow,fragments=require(L+'/rewrite-v1/fragment-proposals.cjs').fragments;
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const D=__dirname,c=JSON.parse(fs.readFileSync(D+'/contract.json'));fs.mkdirSync(D+'/generated');fs.mkdirSync(D+'/generated/sources');let rows=[],attempts=[];
for(const r of c.rows){const input=fs.readFileSync(D+'/'+r.source_file,'utf8');if(sha(input)!==r.source_sha256)throw Error('drift');let n;
try{n=old.normalize(input)}catch(e){
 try {
 const acorn=require('acorn'),gen=require('escodegen'),tree=acorn.parse(input,{ecmaVersion:2022});
 const [impl,wrapper]=tree.body;
 if(tree.body.length!==2||impl.type!=='FunctionDeclaration'||impl.id.name!=='implementation'||wrapper.type!=='FunctionDeclaration'||wrapper.body.body.length!==1)throw e;
 const call=wrapper.body.body[0];
 if(call.type!=='ReturnStatement'||call.argument.type!=='CallExpression'||call.argument.callee.name!=='implementation'||call.argument.arguments.length!==wrapper.params.length||!wrapper.params.every((p,i)=>p.type==='Identifier'&&call.argument.arguments[i].type==='Identifier'&&call.argument.arguments[i].name===p.name))throw e;
 const entry=wrapper.id.name;wrapper.id.name='solve';n={entry,source:gen.generate(tree)+'\n'};
 }catch(reason){attempts.push({id:r.id,status:'unsupported',reason:String(reason)});continue;}
}
const seen=new Set();for(const [variant,make]of [['original',()=>input],['canonical',()=>n.source],['compact',()=>old.compact(n.source)],['scope',()=>rw.rename(n.source,'scope')],['role',()=>rw.rename(n.source,'role')],['scope-arrow',()=>{const a=arrow(n.source);if(a.status!=='rewritten')throw Error(a.reason);return rw.rename(a.source,'scope')}],['role-arrow',()=>{const a=arrow(n.source);if(a.status!=='rewritten')throw Error(a.reason);return rw.rename(a.source,'role')}]]){
try{const text=make(),h=sha(text);if(seen.has(h)){attempts.push({id:r.id,variant,status:'duplicate',sha256:h});continue;}seen.add(h);const file=D+'/generated/sources/'+r.id+'-'+variant+'.js';fs.writeFileSync(file,text);rows.push({id:r.id,variant,file,sha256:h,entry:variant==='original'?n.entry:'solve',interface:'named-function',parent_sha256:r.source_sha256,...(variant==='original'?{fragments:[],excluded:[text]}:fragments(text))});attempts.push({id:r.id,variant,status:'generated',sha256:h});}catch(e){attempts.push({id:r.id,variant,status:'rejected',reason:String(e)})}}
}
if(rows.length>c.limits.max_new_sources)throw Error('cap');fs.writeFileSync(D+'/generated/manifest.json',JSON.stringify({rows,attempts,contract_sha256:sha(fs.readFileSync(D+'/contract.json'))},null,2)+'\n');console.log(JSON.stringify({sources:rows.length,rejected:attempts.filter(r=>r.status==='rejected'||r.status==='unsupported').length}));
