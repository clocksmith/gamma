'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),acorn=require('/usr/share/nodejs/acorn');
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const ident=(n,name)=>n?.type==='Identifier'&&n.name===name;
function walk(node,fn){if(!node||typeof node.type!=='string')return;fn(node);for(const value of Object.values(node)){if(Array.isArray(value))for(const child of value)walk(child,fn);else if(value&&typeof value.type==='string')walk(value,fn);}}
function shape(node){if(Array.isArray(node))return node.map(shape);if(!node||typeof node!=='object')return node;return Object.fromEntries(Object.entries(node).filter(([k])=>!['start','end','raw'].includes(k)).map(([k,v])=>[k,shape(v)]));}
const parse=s=>acorn.parse(s,{ecmaVersion:2022,sourceType:'script'});
const equivalent=(a,b)=>JSON.stringify(shape(a))===JSON.stringify(shape(b));
const frequency=parse('function f(values){const counts=new Map();for(const value of values){counts.set(value,(counts.get(value)||0)+1);}return counts;}').body[0].body.body;
const memberCounter=parse('function f(values,other){const counts=new Set(values);let result=0;for(const value of other){if(counts.has(value))result++;}return result;}').body[0].body.body;
const vowel=parse("values.replace(/[aeiou]/g, '')").body[0].expression;
const lower=parse("values.replace(/[A-Z]/g, value => value.toLowerCase())").body[0].expression;
function normalizeLoop(node){if(node?.type!=='ForOfStatement')return node;return {...node,body:node.body.type==='BlockStatement'?node.body:{type:'BlockStatement',body:[node.body]}};}
function allowed(source){const tree=parse(source);if(!tree.body.every(n=>n.type==='FunctionDeclaration'&&['solve','countValues'].includes(n.id?.name)&&!n.async&&!n.generator&&n.params.every(p=>p.type==='Identifier')))return null;
 const solve=tree.body.find(n=>ident(n.id,'solve'));if(!solve||tree.body.filter(n=>ident(n.id,'solve')).length!==1)return null;
 let unsafe=false;walk(tree,n=>{if(['ThisExpression','Super','MetaProperty','WithStatement'].includes(n.type)||n.type==='Identifier'&&['arguments','Array','eval','Function','globalThis','process','require'].includes(n.name))unsafe=true;});
 if(unsafe)return null;return {tree,solve};}
function functional(source){const data=allowed(source);if(!data)return {status:'unsupported',reason:'unsupported-context',source};const edits=[],rules=[];
 for(const fn of data.tree.body){const body=fn.body.body;
  if(body.length>=2&&equivalent(body[0],frequency[0])&&equivalent(normalizeLoop(body[1]),frequency[1])){
   edits.push({start:body[0].start,end:body[1].end,text:'const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());'});rules.push('frequency-prefix-to-functional-fold');
  }else if(fn===data.solve&&equivalent(body,memberCounter)){
   edits.push({start:body[1].start,end:body[3].end,text:'return Array.from(other).reduce((result, value) => result + counts.has(value), 0);'});rules.push('membership-counter-to-functional-fold');
  }else if(fn===data.solve&&body.length===1&&body[0].type==='ReturnStatement'){
   if(equivalent(body[0].argument,vowel)){edits.push({start:body[0].argument.start,end:body[0].argument.end,text:"Array.from(values).filter(value => !'aeiou'.includes(value)).join('')"});rules.push('vowel-replace-to-filter');}
   else if(equivalent(body[0].argument,lower)){edits.push({start:body[0].argument.start,end:body[0].argument.end,text:"Array.from(values).map(value => value >= 'A' && value <= 'Z' ? value.toLowerCase() : value).join('')"});rules.push('ascii-replace-to-map');}
  }
 }
 if(!edits.length)return {status:'unsupported',reason:'no-supported-pattern',source};let output=source;for(const e of edits.sort((a,b)=>b.start-a.start))output=output.slice(0,e.start)+e.text+output.slice(e.end);parse(output);
 return {status:'rewritten',source:output,rules,edits,domain:'Ordinary dense arrays or strings and unmodified built-ins; occurrence counts remain exact within safe integer bounds. Array.from adds O(n) temporary storage; no input mutation. ASCII replacement affects A-Z only. Strings retain code-point iteration and are rejoined exactly.'};}
function arrow(source){let tree;try{tree=parse(source);}catch{return {status:'unsupported',reason:'parse-rejected',source};}const fn=tree.body.find(n=>n.type==='FunctionDeclaration'&&ident(n.id,'solve'));if(!fn||fn.async||fn.generator||fn.params.some(p=>p.type!=='Identifier'))return {status:'unsupported',reason:'noncanonical-entrypoint',source};
 let unsafe=false;walk(fn.body,n=>{if(['ThisExpression','Super','MetaProperty'].includes(n.type)||n.type==='Identifier'&&['arguments','solve'].includes(n.name))unsafe=true;});if(unsafe)return {status:'unsupported',reason:'function-identity-or-this',source};
 const params=fn.params.map(p=>source.slice(p.start,p.end)).join(', '),single=fn.body.body.length===1&&fn.body.body[0].type==='ReturnStatement'&&fn.body.body[0].argument;
 const body=single?'('+source.slice(single.start,single.end)+')':source.slice(fn.body.start,fn.body.end);
 const output=source.slice(0,fn.start)+`const solve = (${params}) => ${body};`+source.slice(fn.end);parse(output);
 return {status:'rewritten',source:output,rules:[single?'single-return-to-arrow-expression':'entrypoint-to-arrow-block'],domain:'Known top-level solve entrypoint invoked after source evaluation; no function identity, construction, recursion, this or arguments use. Changes declaration/hoisting semantics outside this declared harness contract.'};}
function fragments(source){const tree=parse(source),pieces=new Set([...source]);walk(tree,n=>{pieces.add(source.slice(n.start,n.end));if(n.type==='BlockStatement')for(const statement of n.body)pieces.add(source.slice(statement.start,statement.end));});
 const lines=source.split(/(?<=\n)/);for(let i=0;i<lines.length;i++)for(let j=i+1;j<=Math.min(lines.length,i+3);j++)pieces.add(lines.slice(i,j).join(''));
 return [...pieces].filter(Boolean).sort();}
function main(root,out){if(!root||!out)throw Error('Usage: node generate.cjs LITERALS_ROOT NEW_OUTPUT');if(fs.existsSync(out))throw Error('Output already exists');fs.mkdirSync(out,{recursive:true});fs.mkdirSync(path.join(out,'sources'));
 const frozen=JSON.parse(fs.readFileSync(path.join(root,'pass2/source_manifest.json'))),variants={},attempts=[];
 function add(id,name,source,parent,rules,domain){const sha=hash(source);variants[id]??={};if(Object.values(variants[id]).some(v=>v.sha256===sha))return;const file=`sources/${id}-${name}.js`;fs.writeFileSync(path.join(out,file),source);variants[id][name]={file,sha256:sha,parent,rules,domain};}
 for(const [key,expected] of Object.entries(frozen.source_hashes).sort()){const [id,arm]=key.split('/');if(!['baseline','shared'].includes(arm))continue;const relative=arm==='baseline'?`sources/normalized/${id}.js`:`pass2/sources/shared/${id}.js`;const source=fs.readFileSync(path.join(root,relative),'utf8');if(hash(source)!==expected)throw Error('Frozen source drift '+relative);add(id,arm,source,{path:relative,sha256:expected},[], 'Preserved existing development-qualified source.');
  for(const [label,transform] of [['arrow',arrow],['functional',functional]]){const result=transform(source);attempts.push({problem:id,parent:relative,parent_sha256:expected,method:label,status:result.status,reason:result.reason||null,output_sha256:hash(result.source),rules:result.rules||[],domain:result.domain||null,edits:result.edits||null});if(result.status==='rewritten'){add(id,arm+'-'+label,result.source,{path:relative,sha256:expected},result.rules,result.domain);if(label==='functional'){const a=arrow(result.source);attempts.push({problem:id,parent_sha256:hash(result.source),method:'functional-arrow',status:a.status,output_sha256:hash(a.source),rules:a.rules||[],domain:a.domain||null});if(a.status==='rewritten')add(id,arm+'-functional-arrow',a.source,{sha256:hash(result.source)},[...result.rules,...a.rules],result.domain+' '+a.domain);}}}
 }
 const count=Object.values(variants).reduce((n,v)=>n+Object.keys(v).length,0);if(count>120||Object.keys(variants).length!==20)throw Error('Source budget exceeded');
 const pools={};for(const [id,arms] of Object.entries(variants))for(const [arm,row] of Object.entries(arms))pools[id+'/'+arm]=fragments(fs.readFileSync(path.join(out,row.file),'utf8'));
 const result={schema:'gamma.functional-literals-sources.v1',generator_sha256:hash(fs.readFileSync(__filename)),frozen_source_manifest_sha256:hash(fs.readFileSync(path.join(root,'pass2/source_manifest.json'))),source_count:count,variants,attempts};fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(result,null,2)+'\n');fs.writeFileSync(path.join(out,'fragments.json'),JSON.stringify(pools)+'\n');console.log(JSON.stringify({sources:count,attempts:attempts.length,rewritten:attempts.filter(x=>x.status==='rewritten').length}));}
if(require.main===module)main(...process.argv.slice(2));module.exports={functional,arrow,fragments};
