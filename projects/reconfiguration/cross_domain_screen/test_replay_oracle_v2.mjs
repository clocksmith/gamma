import test from 'node:test';
import assert from 'node:assert/strict';
import {canonicalHash,validateInputs,replay,sha} from './replay_oracle_v2.mjs';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {gzipSync} from 'node:zlib';

const seal=(body,key)=>({...body,[key]:canonicalHash(body)});
function fixture(){
 const conditions=['base','channel_gain','shuffled_context','permuted_gain'];
 const tasks={tasks:Array.from({length:6},(_,i)=>({id:`fixture-${i}`,domain:`domain-${i%3}`,family:`family-${i}`}))};
 const protocol={candidate:{id:'fixture-candidate'},conditions};
 const candidateSha256=canonicalHash(protocol.candidate),hashes={protocol:'a'.repeat(64),tasks:'b'.repeat(64),oldOracle:'c'.repeat(64)};
 const lock=seal({inputHashes:{protocol:hashes.protocol,tasks:hashes.tasks},sources:{'screen/oracles.py':hashes.oldOracle},candidateSha256},'lockSha256');
 const records=tasks.tasks.flatMap(t=>conditions.map(condition=>({id:`${t.id}/${condition}`,taskId:t.id,domain:t.domain,family:t.family,condition,candidateSha256,cacheArm:'mlp_base_cache',source:'CPU fixture only',outputTokens:[1,2],tokenCount:2,gainHash:condition==='base'?null:'d'.repeat(64),timing:{end_to_end_ms:1}})));
 const sealed=seal({candidateSha256,requestCount:24,records},'outputsSha256');
 const scores=records.map(r=>({id:r.id,passed:true}));
 const receipt=seal({status:'exploratory_screen_complete',requestCount:24,lockSha256:lock.lockSha256,outputsSha256:sealed.outputsSha256,candidateSha256,records:structuredClone(records),scores},'receiptSha256');
 const journal=[...records.map(record=>({kind:'request-end',record})),{kind:'outputs-sealed',outputsSha256:sealed.outputsSha256,at:'2026-11-13T13:00:00Z'},...scores.map(record=>({kind:'score',record,at:'2026-11-13T13:00:01Z'}))];
 return {lock,protocol,tasks,receipt,sealed,journal,hashes};
}
test('complete original sealed population and all-score ordering validate',()=>{
 const result=validateInputs(fixture());assert.equal(result.all24OutputsSealedBeforeScoring,true);assert.equal(result.exactSourceTokensGainsTimingPreserved,true);
});
test('tampered source/token/timing and missing samples cannot hide behind recomputed receipt hash',()=>{
 for(const mutate of [x=>x.receipt.records[0].source+=' altered',x=>x.receipt.records[0].outputTokens[0]++,x=>x.receipt.records[0].timing.end_to_end_ms++,x=>x.receipt.records.pop()]){
  const x=fixture();mutate(x);delete x.receipt.receiptSha256;x.receipt=seal(x.receipt,'receiptSha256');assert.throws(()=>validateInputs(x),/Receipt changed sealed/);
 }
});
test('early scoring, wrong original oracle and wrong candidate are rejected',()=>{
 const early=fixture();early.journal.unshift(early.journal.pop());assert.throws(()=>validateInputs(early),/Scoring preceded/);
 const oracle=fixture();oracle.hashes.oldOracle='e'.repeat(64);assert.throws(()=>validateInputs(oracle),/Original oracle differs/);
 const candidate=fixture();candidate.protocol.candidate.id='different';assert.throws(()=>validateInputs(candidate),/Candidate identity/);
});
test('compressed archive cannot substitute bytes with a false raw hash',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'screen-replay-archive-fixture-'));
 try{
  const options={archiveDirectory:dir};
  for(const key of ['lock','protocol','tasks','oldOracle','newOracle']){options[key]=join(dir,key);await writeFile(options[key],'{}');}
  const raw=Buffer.from('{"fixture":true}'),bytes=gzipSync(raw);
  await writeFile(join(dir,'receipt.json.gz'),bytes);
  await writeFile(join(dir,'archive.json'),JSON.stringify({schema:'gamma.cross-domain-screen-archive/v1',originalFilesUnmodified:true,files:[{filename:'receipt.json.gz',compression:'gzip',storedBytes:bytes.length,storedSha256:sha(bytes),rawBytes:raw.length,rawSha256:'0'.repeat(64)}]}));
  await assert.rejects(replay(options),/Archived uncompressed bytes mismatch/);
 }finally{await rm(dir,{recursive:true,force:true});}
});
