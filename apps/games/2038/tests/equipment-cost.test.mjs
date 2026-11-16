import test from 'node:test';
import assert from 'node:assert/strict';
import {fixture,action} from './helpers/smaller-game.mjs';

for (const cost of [2,3]) for (const factionId of ['platform_empire','vertical_empire']) {
  test(`equipment cost ${cost}: ${factionId} affordability, debit, discount and production agree`, async()=>{
    const m=fixture({factionId,rulesVariant:{facilityCost:cost}}),p=m.players[0];
    const price=cost-(factionId==='vertical_empire'?1:0);
    p.runway=price-1;
    assert.equal(m.legalResolutions(0,'build').filter(d=>!d.parameters.skipAction).length,0);
    p.runway=price;
    const d=action(m,0,'build',d=>d.parameters.equipOrgId===d.parameters.pieceId);
    assert.equal(d.parameters.actualRunwayCost,price);
    m.applyResolution(0,d);
    assert.equal(p.runway,0);
    const org=p.pieces.find(o=>o.id===d.parameters.equipOrgId);
    assert.equal(org.equipped,true);
    assert.ok(!m.legalResolutions(0,'build').some(x=>x.parameters.equipOrgId===org.id));
    p.compute=0; await m.produceAll();
    assert.equal(p.compute,4);
    // Capital pricing must not accidentally increase recruitment or add turns.
    p.runway=2;
    const recruit=action(m,0,'organize',d=>d.parameters.mode==='recruit');
    m.applyResolution(0,recruit); assert.equal(p.runway,0); assert.equal(p.pieces.length,3);
  });
}
