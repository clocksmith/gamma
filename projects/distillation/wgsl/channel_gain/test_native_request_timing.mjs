import test from 'node:test';import assert from 'node:assert/strict';import {finishNativeRequest} from './native_request_timing.mjs';
test('native request clock includes async cleanup and final bookkeeping while charging shared setup explicitly',async()=>{
 let now=40;const result={timing:{decode_ms:30}},order=[];
 await finishNativeRequest(result,{startedAt:0,clock:()=>now,inputContractMs:3,setup:{reference_prefill_ms:10,base_prefill_ms:12,gain_ms:2,setup_other_ms:1,setup_cleanup_ms:2},cleanup:async()=>{await Promise.resolve();now+=7;order.push('cleanup');},afterCleanup:()=>{assert.deepEqual(order,['cleanup']);now+=5;order.push('bookkeeping');}});
 assert.equal(result.timing.request_cleanup_ms,7);assert.equal(result.physicalRequestMs,52);assert.equal(result.timing.end_to_end_ms,82);assert.equal(result.timing.decode_ms,30);
});
test('cleanup also executes for failed requests and cannot produce a successful latency receipt on cleanup failure',async()=>{
 let called=false;await finishNativeRequest(undefined,{startedAt:0,cleanup:async()=>{called=true;}});assert.equal(called,true);
 const result={timing:{}};await assert.rejects(finishNativeRequest(result,{startedAt:0,cleanup:async()=>{throw Error('dispose failed');}}),/dispose failed/);assert.equal(result.physicalRequestMs,undefined);assert.equal(result.timing.end_to_end_ms,undefined);
});
