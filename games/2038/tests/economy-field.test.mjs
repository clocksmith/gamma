import test from 'node:test';
import assert from 'node:assert/strict';
import {scenarios,play,CANDIDATES} from '../evidence/studies/2026-10-11-economy-field.mjs';
import {json,profiles} from './helpers/smaller-game.mjs';
const input=Object.fromEntries(await Promise.all(['game-config','factions','headlines','projects','mandates'].map(async n=>[n,await json(n)])));
test('economy confirmation crosses seats and institutions and partitions without repeated seeds',()=>{
  for (const [n,expected] of [[3,960],[4,1920],[5,960]]) {
    const rows=scenarios(n,'greedy'); assert.equal(rows.length,expected);
    assert.equal(new Set(rows.map(b=>b.seed)).size,expected);
    const exposure={};
    for (const b of rows) for(let s=0;s<n;s++) {
      const k=`${s}:${b.institutions[s]}:${(s+b.policyRotation)%4}`;
      exposure[k]=(exposure[k]||0)+1;
    }
    assert.equal(Object.keys(exposure).length,n*6*4);
    assert.equal(new Set(Object.values(exposure)).size,1);
    assert.ok(scenarios(n,'greedy',true).every(b=>!rows.some(r=>r.seed===b.seed)));
    assert.ok(scenarios(n,'weighted').every(b=>!rows.some(r=>r.seed===b.seed)));
  }
});
test('one-lever arms preserve complete games and rich/batch outcomes',async()=>{
  const block={...scenarios(4,'greedy',true)[0],seed:'economy-test-parity'};
  for(const overlay of [{},...Object.values(CANDIDATES)]) {
    const a=await play(input,profiles.slice(0,4),block,overlay);
    assert.deepEqual(a,await play(input,profiles.slice(0,4),block,overlay,'rich'));
    assert.ok(a.players.every(p=>Object.values(p.actions).reduce((x,y)=>x+y,0)===12));
  }
});

test('analysis preserves pairing and rejects out-of-range winner fractions',async()=>{
  const {interval,summarize}=await import('../evidence/studies/2026-10-11-economy-analysis.mjs');
  assert.throws(()=>interval([0,2]),RangeError);
  assert.throws(()=>interval([0]),RangeError);
  assert.equal(interval([0,0]).mean,0);
  const block={...scenarios(4,'greedy',true)[0],seed:'economy-analysis-test'};
  const outcome=await play(input,profiles.slice(0,4),block);
  const summary=summarize([{arms:{canonical:outcome,candidate:outcome}},{arms:{canonical:outcome,candidate:outcome}}]);
  assert.equal(summary.researchEffect.mean,0);
  assert.deepEqual(summary.arms.canonical,summary.arms.candidate);
  assert.ok(Math.abs(Object.values(summary.arms.canonical.winnerActions).reduce((a,b)=>a+b,0)-1)<1e-12);
});
