// Trusted AST-only transformer. Input sources are parsed, never evaluated.
import fs from 'node:fs';
import {fileURLToPath} from 'node:url';
import {acorn,astring} from './parser.mjs';
const {generate}=astring;
import {bindings} from './bindings.mjs';
const parse=text=>acorn.parse(text,{ecmaVersion:2022,ranges:true});
function shape(node){
 if(Array.isArray(node))return node.map(shape);
 if(typeof node==='number'&&(!Number.isFinite(node)||Object.is(node,-0)))return {$number:String(node),negativeZero:Object.is(node,-0)};
 if(node===null||typeof node!=='object')return typeof node==='bigint'?{$bigint:String(node)}:node;
 const out={};for(const key of Object.keys(node).sort()){
  if(['start','end','range','loc','raw'].includes(key))continue;
  // Regex Literal.value is a native RegExp; regex.pattern/flags remain exact.
  if(key==='value'&&node.regex){out.value={$regexp:node.regex};continue;}
  out[key]=shape(node[key]);
 }return out;
}
function same(a,b){return JSON.stringify(shape(a))===JSON.stringify(shape(b));}
export function canonicalize(source,mode='role'){
 if(!['role','format'].includes(mode))throw Error('unsupported mode');
 const original=parse(source),graph=bindings(source);
 if(graph.unsafe)throw Error('unsafe source: '+graph.reason);
 const names=graph.variables.map(v=>v.name),edits=[],changes=[];
 if(mode==='role')for(const v of graph.variables){
  if(!v.eligible)continue;
  let number=0,name;
  do{name=v.role+number++;}while(v.forbidden.includes(name)||v.neighbors.some(i=>names[i]===name));
  names[v.id]=name;
  if(name!==v.name){changes.push({id:v.id,from:v.name,to:name,role:v.role});for(const [a,b] of v.spans)edits.push([a,b,name]);}
 }
 // Final simultaneous assignment satisfies all capture and scope constraints.
 for(const v of graph.variables)if(v.eligible&&(v.forbidden.includes(names[v.id])||v.neighbors.some(i=>names[i]===names[v.id])))throw Error('capture conflict');
 edits.sort((a,b)=>b[0]-a[0]);let renamed=source,last=source.length;
 for(const [a,b,name] of edits){if(b>last)throw Error('overlapping edit');renamed=renamed.slice(0,a)+name+renamed.slice(b);last=a;}
 const intended=parse(renamed),expected=structuredClone(original),bySpan=new Map(edits.map(([a,b,name])=>[a+':'+b,name]));
 function visit(n){if(!n||typeof n!=='object')return;if(n.type==='Identifier'&&bySpan.has(n.start+':'+n.end))n.name=bySpan.get(n.start+':'+n.end);for(const x of Object.values(n))if(Array.isArray(x))x.forEach(visit);else if(x&&typeof x==='object')visit(x);}
 visit(expected);if(!same(expected,intended))throw Error('unexpected AST change');
 const after=bindings(renamed);
 if(after.unsafe||after.variables.length!==graph.variables.length)throw Error('scope graph changed');
 for(const v of graph.variables){const w=after.variables[v.id];if(w.name!==names[v.id]||w.scope!==v.scope||JSON.stringify(w.neighbors)!==JSON.stringify(v.neighbors)||w.spans.length!==v.spans.length)throw Error('binding resolution changed');}
 const output=generate(intended,{indent:'',lineEnd:'\n'});
 if(!same(intended,parse(output)))throw Error('printer changed AST');
 return {source:output,mode,changed_bindings:changes,eligible_bindings:graph.variables.filter(v=>v.eligible).length,ast_verified:true,candidate_executions:0};
}
if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]){
 const input=JSON.parse(fs.readFileSync(0,'utf8')),out={};
 for(const [id,source] of Object.entries(input.sources)){
  try{out[id]={ok:true,...canonicalize(source,input.mode)};}catch(error){out[id]={ok:false,error:String(error)};}
 }
 process.stdout.write(JSON.stringify(out));
}
