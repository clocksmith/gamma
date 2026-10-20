'use strict';
const fs=require('fs'),path=require('path'),crypto=require('crypto'),acorn=require('acorn'),scope=require('eslint-scope'),gen=require('escodegen');
const sha=s=>crypto.createHash('sha256').update(s).digest('hex');
const parse=s=>acorn.parse(s,{ecmaVersion:2022,sourceType:'script',ranges:true});
const emit=t=>gen.generate(t,{format:{indent:{style:'  '},quotes:'single',semicolons:true}})+'\n';
function walk(n,f){if(!n||typeof n.type!=='string')return;f(n);for(const v of Object.values(n)){if(Array.isArray(v)){for(const x of v)walk(x,f);}else if(v&&typeof v.type==='string')walk(v,f);}}
function normal(source){const t=parse(source),classes=t.body.filter(n=>n.type==='ClassDeclaration');if(classes.length!==1||classes[0].id.name!=='Solution')throw Error('Expected one Solution class');const c=classes[0];if(c.superClass||c.body.body.length!==1)throw Error('Unsupported multi-method class');const m=c.body.body[0];if(m.kind!=='method'||m.computed||m.static||m.value.async||m.value.generator)throw Error('Unsupported method');let unsafe=false;walk(m.value.body,n=>{if(['ThisExpression','Super'].includes(n.type))unsafe=true;});if(unsafe)throw Error('Method-dependent this');t.body[t.body.indexOf(c)]={type:'FunctionDeclaration',id:{type:'Identifier',name:'solve'},params:m.value.params,body:m.value.body,generator:false,async:false};return {source:emit(t),method:m.key.name,rules:['single-class-method-to-counted-solve']};}
function canonical(source){let t=parse(source),rules=[];const solve=t.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name==='solve');if(!solve)throw Error('No solve');
 const b=solve.body.body;if(b.length===1&&b[0].type==='ReturnStatement'&&b[0].argument?.type==='CallExpression'){
  const call=b[0].argument,helper=t.body.find(n=>n.type==='FunctionDeclaration'&&n.id.name===call.callee.name&&n!==solve);let refs=0,unsafe=false;
  if(helper){walk(t,n=>{if(n.type==='Identifier'&&n.name===helper.id.name)refs++;});walk(helper.body,n=>{if(n.type==='ThisExpression'||n.type==='Identifier'&&['arguments','eval'].includes(n.name))unsafe=true;});}
  if(helper&&refs===2&&!unsafe&&call.arguments.length===solve.params.length&&helper.params.length===solve.params.length&&call.arguments.every((n,i)=>n.type==='Identifier'&&solve.params[i].type==='Identifier'&&n.name===solve.params[i].name)){
   solve.params=helper.params;solve.body=helper.body;t.body=t.body.filter(n=>n!==helper);rules.push('inline-single-use-tail-delegate-with-identical-positional-arguments');
  }
 }
 t.body=[solve,...t.body.filter(n=>n!==solve)];let printed=emit(t);t=parse(printed);const manager=scope.analyze(t,{ecmaVersion:2022,sourceType:'script',optimistic:false,ignoreEval:false});const used=new Set(manager.globalScope.through.map(r=>r.identifier.name));used.add('solve');const seenNodes=new Map();let helperCount=0;
 function fresh(base){let s=base,i=2;while(used.has(s))s=base+(i++);used.add(s);return s;}
 for(const sc of manager.scopes)for(const v of sc.variables){if(v.name==='arguments'||v.name==='solve'||!v.defs.length)continue;let base='value';const def=v.defs[0],name=v.name;
  if(def.type==='FunctionName')base='helper';
  else if(def.type==='Parameter'){const fn=def.node;const ix=fn.params.findIndex(p=>p===def.name);base=['values','other','target'][ix]||'argument';}
  else if(/count|frequen/i.test(name))base=/counts|frequenc.*by/i.test(name)?'counts':'count';
  else if(/index|bound|position/i.test(name))base='index';
  else if(/result|output|answer/i.test(name))base='result';
  else if(/minimum|lowest|smallest/i.test(name))base='minimum';
  else if(/maximum|highest|largest/i.test(name))base='maximum';
  else if(/sum|total/i.test(name))base='total';
  else if(/left|previous/i.test(name))base='left';
  else if(/right|next/i.test(name))base='right';
  else if(/length|size|width|height/i.test(name))base='size';
  else if(/values|rows|matrix|grid|characters|words|stack/i.test(name))base='items';
  else if(/key/i.test(name))base='key';
  const replacement=fresh(base);for(const n of [...v.identifiers,...v.references.map(x=>x.identifier)])seenNodes.set(n,replacement);
 }
 walk(t,n=>{if(n.type==='Property'&&n.shorthand&&seenNodes.has(n.value)){n.key={...n.key};n.shorthand=false;}if(n.type==='Identifier'&&seenNodes.has(n))n.name=seenNodes.get(n);});rules.push('scope-resolved-alpha-canonicalization-with-capture-avoidance');return {source:emit(t),rules};}
function fingerprint(n){if(!n||typeof n!=='object')return n;if(Array.isArray(n))return n.map(fingerprint);const out={};for(const[k,v]of Object.entries(n)){if(['start','end','range','raw'].includes(k))continue;if(k==='name'&&n.type==='Identifier'){out[k]='ID';continue;}if(k==='value'&&n.type==='Literal'){out[k]=typeof v;continue;}out[k]=fingerprint(v);}return out;}
function features(source){const t=parse(source),frags=new Set([...source]),structures=new Set();walk(t,n=>{const s=source.slice(n.start,n.end);if(s.length>=8){frags.add(s);structures.add(sha(JSON.stringify(fingerprint(n))));}});const lines=source.split(/(?<=\n)/);for(let i=0;i<lines.length;i++)for(let j=i+1;j<=Math.min(i+3,lines.length);j++)frags.add(lines.slice(i,j).join(''));return {fragments:[...frags].sort(),structural_signatures:[...structures].sort()};}
function main(root,exportRoot,out,phase){if(!['fit','heldback'].includes(phase))throw Error('phase');const c=JSON.parse(fs.readFileSync(path.join(root,'contract.json')));if(phase==='heldback'&&!fs.existsSync(path.join(root,'vocabulary-freeze.json')))throw Error('Heldback access requires vocabulary freeze');if(fs.existsSync(out))throw Error('Output exists');fs.mkdirSync(out,{recursive:true});fs.mkdirSync(path.join(out,'sources'));const ids=Object.values(c.clusters).flatMap(v=>v[phase]).sort((a,b)=>a-b),rows=[],failures=[],pools={};
 for(const id of ids){const entry=c.selected[id],original=fs.readFileSync(path.join(exportRoot,entry.relative_path),'utf8');if(sha(original)!==entry.sha256)throw Error('Source hash mismatch');const prefix=String(id).padStart(4,'0');fs.writeFileSync(path.join(out,'sources',prefix+'-original.js'),original);
  try{const n=normal(original),k=canonical(n.source);for(const [variant,result]of [['normalized',n],['canonical',k]]){const file='sources/'+prefix+'-'+variant+'.js';fs.writeFileSync(path.join(out,file),result.source);rows.push({id,variant,file,sha256:sha(result.source),original_sha256:entry.sha256,method:n.method,rules:result.rules});pools[prefix+'/'+variant]=features(result.source);}rows.push({id,variant:'original',file:'sources/'+prefix+'-original.js',sha256:entry.sha256,original_sha256:entry.sha256,method:n.method,rules:[]});}
  catch(error){failures.push({id,error:String(error),source_preserved:true});}
 }
 const m={schema:'gamma.cluster-sources.v1',phase,contract_sha256:sha(fs.readFileSync(path.join(root,'contract.json'))),generator_sha256:sha(fs.readFileSync(__filename)),rows,failures};fs.writeFileSync(path.join(out,'manifest.json'),JSON.stringify(m,null,2)+'\n');fs.writeFileSync(path.join(out,'features.json'),JSON.stringify(pools)+'\n');console.log(JSON.stringify({phase,problems:ids.length,source_variants:rows.length,failures}));}
if(require.main===module)main(...process.argv.slice(2));module.exports={normal,canonical,features};
