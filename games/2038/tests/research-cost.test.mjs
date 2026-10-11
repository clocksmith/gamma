import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture,config,action,policies} from './helpers/smaller-game.mjs';

test('Research reads its declared cost for affordability, preview and payment',async()=>{
  const altered=structuredClone(config);altered.actionEffects.research.computeCost=2;
  const m=fixture({config:altered});const p=m.players[0];p.compute=1;
  assert.equal(m.legalResolutions(0,'research').length,0);
  p.compute=2;const d=action(m,0,'research');
  assert.equal(d.consequences.compute,-2);assert.match(d.label,/Pay 2 Compute/);
  await m.research(policies(m,packet=>packet.legalDecisions.find(d=>d.decisionId==='research_bank')),0,d);
  assert.equal(p.compute,0);
});
