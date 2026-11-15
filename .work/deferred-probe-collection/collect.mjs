import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
const [attemptArg,outArg,lockArg]=process.argv.slice(2),attempt=resolve(attemptArg),out=resolve(outArg);
const hash=b=>createHash('sha256').update(b).digest('hex');
const canon=v=>Array.isArray(v)?v.map(canon):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canon(v[k])])):v;
const canonicalHash=v=>hash(JSON.stringify(canon(v)));
const journal=JSON.parse('['+(await readFile(join(attempt,'scheduler.jsonl'),'utf8')).trim().split('\n').join(',')+']');
if(!journal.some(e=>e.kind==='probe-process-ended'||e.kind==='scheduler-error'))throw Error('Scheduler is not terminal');
const files=['scheduler.jsonl','probe-stdout.log','probe-output/journal.jsonl','probe-output/sealed-outputs.json','probe-output/receipt.json'];
await mkdir(out);
const entries=[],parsed={};
for(const name of files){let raw;try{raw=await readFile(join(attempt,name));}catch(e){if(e.code==='ENOENT')continue;throw e;}
const filename=name.replaceAll('/','-')+'.gz',stored=gzipSync(raw,{level:9});await writeFile(join(out,filename),stored,{flag:'wx'});
entries.push({sourcePath:join(attempt,name),filename,compression:'gzip',rawBytes:raw.length,rawSha256:hash(raw),storedBytes:stored.length,storedSha256:hash(stored)});
if(name.endsWith('.json'))parsed[name]=JSON.parse(raw);else if(name.endsWith('.jsonl'))parsed[name]=raw.toString().trim().split('\n').map(x=>JSON.parse(x));}
const lock=JSON.parse(await readFile(lockArg));const{lockSha256,...lockBody}=lock;if(canonicalHash(lockBody)!==lockSha256)throw Error('Lock checksum mismatch');
const validations=[];
for(const[name,field]of [['probe-output/receipt.json','receiptSha256'],['probe-output/sealed-outputs.json','outputsSha256']])if(parsed[name]){const{[field]:expected,...body}=parsed[name],actual=canonicalHash(body);if(expected!==actual)throw Error(`${name} canonical checksum mismatch`);validations.push({name,field,expected,actual,passed:true});}
const receipt=parsed['probe-output/receipt.json'],events=parsed['probe-output/journal.jsonl']??[],sealed=parsed['probe-output/sealed-outputs.json'];
const sealIndex=events.findIndex(e=>e.kind==='outputs-sealed'),scoreIndices=events.flatMap((e,i)=>e.kind==='public-score'?[i]:[]);
if(receipt){if(receipt.status!=='mechanics_probe_complete'||receipt.lockSha256!==lockSha256||receipt.requestCount!==4||receipt.results.length!==4||receipt.resetDiagnostics.length!==2||receipt.confirmationEvaluated!==false)throw Error('Probe completion contract mismatch');
if(receipt.outputsSha256!==sealed?.outputsSha256||canonicalHash(receipt.results)!==canonicalHash(sealed.results))throw Error('Sealed outputs differ from scored receipt');
if(sealIndex<0||scoreIndices.length!==4||scoreIndices.some(i=>i<=sealIndex))throw Error('Scoring preceded sealing');}
const validation={schema:'gamma.deferred-probe-artifact-validation/v1',canonicalIdentities:validations,lockSha256,receiptStatus:receipt?.status??null,requestEndCount:events.filter(e=>e.kind==='request-end').length,allScoresAfterSeal:scoreIndices.length===4&&scoreIndices.every(i=>i>sealIndex),schedulerTerminal:journal.filter(e=>['probe-process-ended','scheduler-error','exclusive-timing-lock-released'].includes(e.kind))};
const summary=receipt?{...Object.fromEntries(Object.entries(receipt).filter(([k])=>!['results','preparations'].includes(k))),results:receipt.results.map(r=>({id:r.id,taskId:r.taskId,condition:r.condition,source:r.source,tokenCount:r.tokenCount,gainHash:r.gainHash,reachedOutputCap:r.reachedOutputCap,physicalRequestMs:r.physicalRequestMs,timing:r.timing,selectedGainLogicalBytes:r.memory?.selectedGainLogicalBytes,selectedGainGpuBytes:r.memory?.gainBytes})),preparations:receipt.preparations.map(p=>({taskId:p.taskId,actualPreparationMs:p.actualPreparationMs})),phaseEvents:events.filter(e=>!['token-contract','preparation-end','request-end','public-score'].includes(e.kind)),schedulerEvents:journal.filter((e,i)=>!e.kind.startsWith('waiting-')||i===journal.findIndex(x=>x.kind===e.kind))}:validation;
for(const[name,value]of [['archive.json',{schema:'gamma.deferred-probe-archive/v1',createdAt:new Date().toISOString(),originalFilesUnmodified:true,files:entries}],['validation.json',validation],['summary.json',summary]])await writeFile(join(out,name),JSON.stringify(value,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({out,status:receipt?.status??'failed_attempt',validation}));
