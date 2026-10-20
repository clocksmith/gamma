import assert from 'node:assert/strict';
import fs from 'node:fs';
import {webcrypto} from 'node:crypto';
globalThis.crypto??=webcrypto;
const root=new URL('./',import.meta.url).href;
const {verifyLanguage,LiteralSession,replayRecord,inspect,sha256,MAX_BITS}=await import(root+'literal-input.js');
const data=await verifyLanguage(JSON.parse(fs.readFileSync(new URL(root+'literal-language.json'))));
const tests=[];async function test(name,fn){await fn();tests.push(name);}
const word=i=>i.toString(2).padStart(7,'0');
await test('all20 exact source hashes, finish and replay',async()=>{for(const p of data.problems){const s=new LiteralSession(data,p.id);for(const b of p.sequence.map(word).join('')+word(127))s.bit(Number(b));const state=s.snapshot();assert(state.complete);assert.equal(await sha256(state.source),p.source_sha256);assert.equal(state.control_bits,7);assert.equal(state.source_only_bits,p.sequence.length*7);const r=await s.report(),replay=await replayRecord(data,r);assert.equal(replay.snapshot().source,state.source);assert.throws(()=>replay.bit(0),/read-only/);}});
await test('all46 unused IDs deterministic and correctable',()=>{for(let id=79;id<=124;id++){const s=new LiteralSession(data,'0242');for(const b of word(id))s.bit(Number(b));assert.match(s.snapshot().error,new RegExp(`ID ${id}`));assert.throws(()=>s.bit(0),/Undo/);s.backspace();assert.equal(s.snapshot().error,null);}});
await test('partial controls reset undo accounting',()=>{const s=new LiteralSession(data,'0242');for(const b of [0,125,1,126,2,127].map(word).join(''))s.bit(Number(b));const x=s.snapshot();assert.deepEqual(x.selected,[2]);assert.equal(x.literal_bits,21);assert.equal(x.control_bits,21);assert.equal(x.total_bits,42);s.backspace();assert.equal(s.snapshot().complete,false);assert.equal(s.snapshot().prefix.length,6);});
await test('replay rejects tampered bits selections hashes costs actions',async()=>{const s=new LiteralSession(data,'0242');s.bit(0);const r=await s.report();for(const key of ['bits','selections','source_sha256','cost','profile','dictionary_sha256']){const altered=structuredClone(r);altered[key]='tampered';await assert.rejects(()=>replayRecord(data,altered));}const bad=structuredClone(r);bad.events=[{kind:'load',source:'injected'}];await assert.rejects(()=>replayRecord(data,bad));});
await test('frozen identity and limits',async()=>{const bad=structuredClone(data);bad.literals[0]+=' ';await assert.rejects(()=>verifyLanguage(bad));assert.throws(()=>inspect('0'.repeat(MAX_BITS+1),data.literals));assert.throws(()=>inspect('2',data.literals));const s=new LiteralSession(data,'0242');assert.throws(()=>s.bit(true));});
await test('report captures one state despite concurrent input',async()=>{const s=new LiteralSession(data,'0242');s.bit(0);const pending=s.report();s.bit(1);const r=await pending;assert.equal(r.bits,'0');assert.equal(r.events.length,1);await replayRecord(data,r);});
console.log(JSON.stringify({passed:tests.length,tests,programs:20,unused_ids_checked:46},null,2));
