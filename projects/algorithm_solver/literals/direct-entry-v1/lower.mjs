// AST-audited entry lowering only. Submitted source is never evaluated.
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {acorn} from '../role-canonical-v1/parser.mjs';
const parse=source=>acorn.parse(source,{ecmaVersion:2022,ranges:true});
function walk(n,fn){if(!n||typeof n!=='object')return;if(n.type)fn(n);for(const x of Object.values(n))if(Array.isArray(x))x.forEach(y=>walk(y,fn));else if(x&&typeof x==='object')walk(x,fn);}
function shape(n){
 if(typeof n==='number'&&(!Number.isFinite(n)||Object.is(n,-0)))return {$number:String(n),negativeZero:Object.is(n,-0)};
 if(n===null||typeof n!=='object')return typeof n==='bigint'?{$bigint:String(n)}:n;
 if(Array.isArray(n))return n.map(shape);
 const out={};for(const k of Object.keys(n).sort()){
  if(['start','end','range','loc','raw'].includes(k))continue;
  out[k]=k==='value'&&n.regex?{$regexp:n.regex}:shape(n[k]);
 }return out;
}
const equal=(a,b)=>JSON.stringify(shape(a))===JSON.stringify(shape(b));
export function lower(source){
 const ast=parse(source),classes=ast.body.filter(n=>n.type==='ClassDeclaration'&&n.id?.name==='Solution'),adapters=ast.body.filter(n=>n.type==='FunctionDeclaration'&&n.id?.name==='solve');
 if(classes.length!==1||adapters.length!==1)throw Error('requires one Solution class and one solve adapter');
 const cls=classes[0],adapter=adapters[0];
 if(cls.superClass||cls.body.body.length!==1)throw Error('requires unextended single-method class');
 const method=cls.body.body[0],fn=method.value;
 if(method.type!=='MethodDefinition'||method.kind!=='method'||method.static||method.computed||method.key.type!=='Identifier'||fn.async||fn.generator||fn.params.some(p=>p.type!=='Identifier')||new Set(fn.params.map(p=>p.name)).size!==fn.params.length)throw Error('unsupported method or parameter semantics');
 const expectedAdapter=parse(`function solve(...args){return new Solution().${method.key.name}(...args);}`).body[0];
 if(!equal(adapter,expectedAdapter))throw Error('adapter differs from fully charged uniform calling contract');
 const bannedNames=new Set(['eval','Function','Reflect','Proxy','globalThis','window','global','process','require','module','exports','Error']);
 const bannedProperties=new Set(['name','toString','constructor','prototype','caller','callee','stack']);
 for(const top of ast.body){
  if(top===adapter)continue;
  walk(top,n=>{
   if(n===cls.id)return;
   if(n.type==='Identifier'&&(bannedNames.has(n.name)||n.name==='Solution'||n.name==='solve'))throw Error('class/entry/global reflection reference');
   if(n.type==='MemberExpression'&&((!n.computed&&bannedProperties.has(n.property.name))||(n.computed&&n.property.type==='Literal'&&bannedProperties.has(n.property.value))))throw Error('reflection property guard');
  });
 }
 walk(fn.body,n=>{if(['ThisExpression','Super','MetaProperty','PrivateIdentifier','StaticBlock'].includes(n.type))throw Error('method receiver or construction semantics');});
 // Keep helper and method-body bytes verbatim. Only the entry signature, explicit
 // strict directive, class boundary and already-charged adapter are replaced.
 const body=source.slice(fn.body.start+1,fn.body.end-1),params=fn.params.map(p=>p.name).join(',');
 const replacement=`function solve(${params}){"use strict";${body}}`;
 const replacementAst=parse(replacement).body[0];
 if(!equal(replacementAst.params,fn.params)||!equal(replacementAst.body.body.slice(1),fn.body.body)||replacementAst.body.body[0].directive!=='use strict')throw Error('method body changed during entry construction');
 const edits=[[cls.start,cls.end,replacement],[adapter.start,adapter.end,'']].sort((a,b)=>b[0]-a[0]);let output=source;
 for(const [a,b,text] of edits)output=output.slice(0,a)+text+output.slice(b);
 const expected=structuredClone(ast);expected.body=ast.body.filter(n=>n!==adapter).map(n=>n===cls?replacementAst:n);
 if(!equal(parse(output),expected))throw Error('unexpected program AST change');
 return {source:output,ast_verified:true,method:method.key.name,source_bytes:Buffer.byteLength(source),lowered_bytes:Buffer.byteLength(output),strict_directive_added:true,helpers_verbatim:true,candidate_executions:0};
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
 const input=JSON.parse(fs.readFileSync(0,'utf8')),out={};
 for(const [id,source] of Object.entries(input.sources))try{out[id]={ok:true,...lower(source)};}catch(error){out[id]={ok:false,error:String(error)};}
 process.stdout.write(JSON.stringify(out));
}
