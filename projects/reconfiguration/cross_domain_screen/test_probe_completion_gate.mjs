import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {checkCompletion,checkInheritedExclusiveLock} from './probe_completion_gate.mjs';
import {hashCanonical} from './runner.mjs';
import {runProbe} from './probe.mjs';
const expected={confirmationStatus:'confirmation_executed',confirmationRequests:176,runtimeLockSha256:'runtime',stageLockSha256:'stage'};
test('completion waits for a terminal receipt and validates self hash, identity and count',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'probe-gate-')),path=join(dir,'receipt.json');
 const body={status:expected.confirmationStatus,confirmationEvaluated:true,runtimeLockSha256:'runtime',stageLockSha256:'stage',generated:{requests:Array.from({length:176},(_,id)=>({id}))}};
 const save=async b=>writeFile(path,JSON.stringify({...b,receiptSha256:hashCanonical(b)}));
 try{
  assert.equal((await checkCompletion(path,expected)).reason,'receipt_missing');
  await writeFile(path,'{');assert.equal((await checkCompletion(path,expected)).reason,'receipt_write_incomplete');
  await save({...body,status:'running'});assert.equal((await checkCompletion(path,expected)).ready,false);
  await save(body);assert.equal((await checkCompletion(path,expected)).requestCount,176);
  await save({...body,generated:{requests:[]}});await assert.rejects(checkCompletion(path,expected),/count/);
  await save({...body,runtimeLockSha256:'other'});await assert.rejects(checkCompletion(path,expected),/runtimeLockSha256/);
  await writeFile(path,JSON.stringify({...body,receiptSha256:'tampered'}));await assert.rejects(checkCompletion(path,expected),/checksum/);
 }finally{await rm(dir,{recursive:true,force:true});}
});
test('direct probe cannot omit the inherited timing lock',async()=>{
 await assert.rejects(runProbe({gpuAuthorized:true}),/timing-lock FD/);
 await assert.rejects(checkInheritedExclusiveLock(-1,'unused'),/FD required/);
});
