// CPU-only replay of the exact archived screen. No inference/runtime imports.
import {createHash} from 'node:crypto';
import {readFile,writeFile} from 'node:fs/promises';
import {gunzipSync} from 'node:zlib';
import {spawnSync} from 'node:child_process';
import {join,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';

const requireThat=(condition,message)=>{if(!condition)throw Error(message);};
export const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export function canonicalHash(value){
 const hash=createHash('sha256');
 function add(v){
  if(Array.isArray(v)){hash.update('[');v.forEach((item,i)=>{if(i)hash.update(',');add(item);});hash.update(']');}
  else if(v&&typeof v==='object'){hash.update('{');Object.keys(v).sort().forEach((key,i)=>{if(i)hash.update(',');hash.update(JSON.stringify(key)+':');add(v[key]);});hash.update('}');}
  else hash.update(JSON.stringify(v));
 }
 add(value);return hash.digest('hex');
}
function validateHash(value,key){const {[key]:expected,...body}=value;requireThat(canonicalHash(body)===expected,`${key} integrity mismatch`);}
export function validateInputs({lock,protocol,tasks,receipt,sealed,journal,hashes}){
 validateHash(lock,'lockSha256');validateHash(receipt,'receiptSha256');validateHash(sealed,'outputsSha256');
 requireThat(lock.inputHashes.protocol===hashes.protocol&&lock.inputHashes.tasks===hashes.tasks,'Original protocol/task file binding mismatch');
 requireThat(lock.sources['screen/oracles.py']===hashes.oldOracle,'Original oracle differs from generation lock');
 requireThat(receipt.status==='exploratory_screen_complete'&&receipt.requestCount===24&&sealed.requestCount===24,'Only a completed24-output screen is replayable');
 requireThat(receipt.lockSha256===lock.lockSha256&&receipt.outputsSha256===sealed.outputsSha256,'Receipt/lock/seal identity mismatch');
 requireThat(lock.candidateSha256===sealed.candidateSha256&&receipt.candidateSha256===sealed.candidateSha256&&canonicalHash(protocol.candidate)===sealed.candidateSha256,'Candidate identity mismatch');
 const rows=tasks.tasks??tasks,expected=rows.flatMap(task=>protocol.conditions.map(condition=>`${task.id}/${condition}`));
 requireThat(rows.length===6&&expected.length===24&&new Set(expected).size===24,'Fixed six-task four-condition population required');
 requireThat(canonicalHash(sealed.records.map(r=>r.id))===canonicalHash(expected),'Sealed task/condition population or order differs');
 requireThat(canonicalHash(receipt.records)===canonicalHash(sealed.records),'Receipt changed sealed source, tokens, gains or timings');
 requireThat(receipt.scores.length===24&&canonicalHash(receipt.scores.map(s=>s.id))===canonicalHash(expected),'Original score population mismatch');
 for(const r of sealed.records){
  const task=rows.find(t=>t.id===r.taskId);
  requireThat(r.id===`${r.taskId}/${r.condition}`&&task&&r.domain===task.domain&&r.family===task.family,'Record task identity mismatch');
  requireThat(r.candidateSha256===sealed.candidateSha256&&r.cacheArm==='mlp_base_cache','Record intervention changed');
  requireThat(typeof r.source==='string'&&Array.isArray(r.outputTokens)&&r.tokenCount===r.outputTokens.length,'Record source/token contract invalid');
 }
 let seenSeal=false,sealAt=null;const ended=[],scores=[];
 for(const event of journal){
  if(event.kind==='request-end'){requireThat(!seenSeal,'Generation appeared after output seal');ended.push(event.record);}
  if(event.kind==='outputs-sealed'){requireThat(!seenSeal&&ended.length===24&&event.outputsSha256===sealed.outputsSha256,'Invalid or premature output seal');seenSeal=true;sealAt=event.at;}
  if(event.kind==='score'){requireThat(seenSeal&&Date.parse(event.at)>=Date.parse(sealAt),'Scoring preceded complete output seal');scores.push(event.record);}
 }
 requireThat(seenSeal&&canonicalHash(ended)===canonicalHash(sealed.records),'Journal did not preserve the exact24 sealed requests');
 requireThat(canonicalHash(scores)===canonicalHash(receipt.scores),'Original scores differ from journal');
 return {all24OutputsSealedBeforeScoring:true,sealedAt:sealAt,exactSourceTokensGainsTimingPreserved:true};
}
function score(python,oracle,record){
 const result=spawnSync(python,['-I',oracle],{input:JSON.stringify({taskId:record.taskId,source:record.source,phase:'both'}),encoding:'utf8',timeout:15000,maxBuffer:1_000_000});
 requireThat(!result.error&&result.status===0,`Oracle subprocess failed: ${result.error?.message??result.stderr}`);
 const value=JSON.parse(result.stdout);requireThat(value.taskId===record.taskId&&typeof value.publicPassed==='boolean'&&typeof value.heldoutPassed==='boolean'&&typeof value.passed==='boolean','Malformed oracle score');
 return {id:record.id,...value,wrongAcceptance:value.publicPassed&&!value.heldoutPassed};
}
function summary(scores,records,protocol,tasks){
 const conditions={};for(const condition of protocol.conditions){const values=scores.filter(s=>records.find(r=>r.id===s.id).condition===condition);conditions[condition]={publicPassed:values.filter(s=>s.publicPassed).length,heldoutPassed:values.filter(s=>s.heldoutPassed).length,semanticPassed:values.filter(s=>s.passed).length,wrongAcceptances:values.filter(s=>s.wrongAcceptance).length,taskCount:tasks.length};}
 const paired={};for(const condition of protocol.conditions.slice(1)){let wins=0,losses=0,ties=0;for(const task of tasks){const base=scores.find(s=>s.id===`${task.id}/base`).passed,changed=scores.find(s=>s.id===`${task.id}/${condition}`).passed;if(changed&&!base)wins++;else if(base&&!changed)losses++;else ties++;}paired[condition]={wins,losses,ties};}
 return {conditions,paired};
}
export async function replay(options){
 const started=performance.now(),files={};
 for(const key of ['lock','protocol','tasks','oldOracle','newOracle']){const bytes=await readFile(options[key]);files[key]={path:options[key],sha256:sha(bytes),bytes:bytes.length,value:key.endsWith('Oracle')?null:JSON.parse(bytes)};}
 const archivePath=join(options.archiveDirectory,'archive.json'),archiveBytes=await readFile(archivePath),archive=JSON.parse(archiveBytes);
 requireThat(archive.schema==='gamma.cross-domain-screen-archive/v1'&&archive.originalFilesUnmodified===true,'Original archive manifest required');
 const artifacts={};
 for(const name of ['receipt.json.gz','sealed-outputs.json.gz','journal.jsonl.gz']){
  const entry=archive.files.find(f=>f.filename===name);requireThat(entry&&entry.compression==='gzip','Missing original archived artifact');
  const bytes=await readFile(join(options.archiveDirectory,name));requireThat(bytes.length===entry.storedBytes&&sha(bytes)===entry.storedSha256,'Archived compressed bytes mismatch');
  const raw=gunzipSync(bytes);requireThat(raw.length===entry.rawBytes&&sha(raw)===entry.rawSha256,'Archived uncompressed bytes mismatch');
  artifacts[name]=name==='journal.jsonl.gz'?raw.toString().trimEnd().split('\n').map(line=>JSON.parse(line)):JSON.parse(raw);
 }
 const {value:lock}=files.lock,{value:protocol}=files.protocol,{value:taskData}=files.tasks;
 const receipt=artifacts['receipt.json.gz'],sealed=artifacts['sealed-outputs.json.gz'];
 const validation=validateInputs({lock,protocol,tasks:taskData,receipt,sealed,journal:artifacts['journal.jsonl.gz'],hashes:Object.fromEntries(Object.entries(files).map(([k,v])=>[k,v.sha256]))});
 // Only the interpreter class may differ. Expected cases, exact-answer oracle,
 // strict output parser and semantic/public combination remain AST-identical.
 const astScript=`import ast,hashlib,json,sys\ndef outside(path):\n tree=ast.parse(open(path).read())\n tree.body=[n for n in tree.body if not (isinstance(n,ast.ClassDef) and n.name=='BoundedPython')]\n return ast.dump(tree,include_attributes=False)\na,b=map(outside,sys.argv[1:]);assert a==b,'Non-interpreter oracle semantics changed';print(json.dumps({'nonInterpreterAstSha256':hashlib.sha256(a.encode()).hexdigest(),'behavioralCasesAndScoringAstIdentical':True}))`;
 const astResult=spawnSync(options.python??'python3',['-I','-c',astScript,options.oldOracle,options.newOracle],{encoding:'utf8',timeout:15000});requireThat(astResult.status===0,`Oracle scope check failed: ${astResult.stderr}`);
 const oldScores=[],newScores=[],changes=[];
 for(const record of sealed.records){
  const oldScore=score(options.python??'python3',options.oldOracle,record);requireThat(canonicalHash(oldScore)===canonicalHash(receipt.scores.find(s=>s.id===record.id)),`Original score could not be reproduced: ${record.id}`);
  const newScore=score(options.python??'python3',options.newOracle,record);oldScores.push(oldScore);newScores.push(newScore);
  if(canonicalHash(oldScore)!==canonicalHash(newScore))changes.push({id:record.id,taskId:record.taskId,condition:record.condition,sourceSha256:sha(record.source),oldScore,newScore});
 }
 const tasks=taskData.tasks??taskData,report={schema:'gamma.cross-domain-oracle-replay/v2',status:'exploratory_sealed_output_replay_complete',createdAt:new Date().toISOString(),
  generationLockSha256:lock.lockSha256,outputsSha256:sealed.outputsSha256,originalReceiptSha256:receipt.receiptSha256,requestCount:24,
  provenance:{files:Object.fromEntries(Object.entries(files).map(([k,{value,...v}])=>[k,v])),archive:{path:archivePath,sha256:sha(archiveBytes)},originalArtifacts:archive.files,replaySourceSha256:sha(await readFile(fileURLToPath(import.meta.url)))},
  validation:{...validation,...JSON.parse(astResult.stdout),original24ScoresReproduced:true},
  acceptanceChange:'Versioned syntax interpretation/expansion: allow bounded pure inline lambdas and ordinary sorted key/reverse keywords. The prompt allowed sorted but did not explicitly specify inline lambda/keyword support; the original restricted grammar is preserved. Behavioral expected cases, exact answers, strict output formatting and pass combination remain unchanged.',
  originalRestrictedGrammar:summary(oldScores,sealed.records,protocol,tasks),correctedBehavioralReplay:summary(newScores,sealed.records,protocol,tasks),changes,scores:newScores,
  sampleIdentity:sealed.records.map(r=>({id:r.id,sourceSha256:sha(r.source),outputTokensSha256:canonicalHash(r.outputTokens),gainHash:r.gainHash,tokenCount:r.tokenCount})),
  generationCostsUnchanged:true,replayCpuWallMs:performance.now()-started,newModelCalls:0,newGpuCalls:0,newSamples:0,selectionOrReranking:false,
  evidenceClass:'Exploratory verified evaluator repair on existing sealed samples, not confirmation. Original scores retained separately; no broad transfer or efficiency claim.'};
 report.replaySha256=canonicalHash(report);
 if(options.output)await writeFile(options.output,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
 if(options.markdown){const lines=['# Corrected sealed-output replay','',report.evidenceClass,'',report.acceptanceChange,'','| Condition | Original restricted semantic pass | Corrected behavioral semantic pass | Corrected wrong acceptances |','| --- | ---: | ---: | ---: |'];for(const c of protocol.conditions)lines.push(`| ${c} | ${report.originalRestrictedGrammar.conditions[c].semanticPassed}/6 | ${report.correctedBehavioralReplay.conditions[c].semanticPassed}/6 | ${report.correctedBehavioralReplay.conditions[c].wrongAcceptances} |`);lines.push('',`Replayed all24 original sealed outputs. New model/GPU calls:0. Changed score records:${changes.length}. Original generation costs unchanged; CPU replay wall:${report.replayCpuWallMs.toFixed(3)}ms.`, '', 'Paired corrected outcomes against base:');for(const[c,v]of Object.entries(report.correctedBehavioralReplay.paired))lines.push(`- ${c}: ${v.wins}wins, ${v.losses}losses, ${v.ties}ties.`);lines.push('',`Old oracle SHA256:${files.oldOracle.sha256}. New oracle SHA256:${files.newOracle.sha256}.`,`Original outputs seal:${sealed.outputsSha256}. Replay:${report.replaySha256}.`);await writeFile(options.markdown,lines.join('\n')+'\n',{flag:'wx'});}
 return report;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 try{const options={};for(let i=2;i<process.argv.length;i+=2){requireThat(process.argv[i].startsWith('--')&&process.argv[i+1],'Expected --option value');options[process.argv[i].slice(2).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=process.argv[i+1];}for(const k of ['archiveDirectory','lock','protocol','tasks','oldOracle','newOracle','output','markdown'])requireThat(options[k],`Missing --${k}`);const r=await replay(options);console.log(JSON.stringify({status:r.status,changes:r.changes.map(x=>x.id),original:r.originalRestrictedGrammar,corrected:r.correctedBehavioralReplay,replayCpuWallMs:r.replayCpuWallMs}));}catch(error){console.error(error.stack??String(error));process.exitCode=2;}
}
