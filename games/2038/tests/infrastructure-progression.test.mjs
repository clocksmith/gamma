import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import { createInteractiveGame } from '../lab/runtime/create-interactive-game.js';

async function setup(count = 3) {
  const { match } = await createInteractiveGame({ playerCount: count, seed: 'personal-infrastructure' }, () => {});
  await match.beginRound([]);
  const tiles = match.board.filter(t => t.category !== 'frontier');
  for (const p of match.players) Object.assign(p, { runway: 12, compute: 10, scrutiny: 0,
    facilities: [{id: `s${p.seat}-facility-1`, tileId: tiles[p.seat].instanceId, category: tiles[p.seat].category}] });
  match.choose = async (_policies, _seat, _stage, choices) => choices[0];
  return match;
}
const choices = (m, seat, id) => m.legalResolutions(seat, 'build').filter(c => c.parameters.project?.id === id);
const alone = (m, seat, id) => choices(m, seat, id).find(c => !c.parameters.facility);

test('personal chips preserve II / III / IV and all earlier unlocks', async () => {
  const data=JSON.parse(await readFile(new URL('../dist/runtime/projects.json',import.meta.url)));
  assert.equal(data.chipsPerFaction,3);
  assert.deepEqual(data.projects.map(p=>[p.id,p.unlockedRound]),[['mega_cluster',2],['fusion_demonstrator',3],['quantum',4]]);
  for(const era of [1,2,3,4]) {
    const m=await setup(); m.round=era;
    for(const p of data.projects) assert.equal(Boolean(alone(m,0,p.id)),era>=p.unlockedRound,p.id);
  }
});

test('every institution can stack all three projects on one host once, without immediate rewards', async()=>{
 for(const count of [2,3,4,5]) {
  const m=await setup(count); m.round=4;
  for(const p of m.players) {
   m.synchronizePublicMandate(p,'fixture');const before={capability:p.capability,mandate:p.mandate};
   for(const id of ['quantum','fusion_demonstrator','mega_cluster']) {
    const plan=alone(m,p.seat,id);assert.ok(plan);
    m.applyBuild(p.seat,plan);
    assert.equal(choices(m,p.seat,id).length,0);
    assert.throws(()=>m.applyBuild(p.seat,plan),/no longer legal/);
   }
   assert.equal(p.runway,3);assert.equal(p.compute,7);assert.equal(p.scrutiny,3);
   assert.equal(p.capability,before.capability);assert.equal(p.mandate,before.mandate);
   assert.equal(new Set(p.projects.map(x=>x.hostId)).size,1);assert.equal(p.generators.length,0);
   assert.deepEqual(m.snapshot().players[p.seat].projects,p.projects);
   assert.deepEqual(m.publicObservation(p.seat).publicTable.players[p.seat].projects,p.projects);
  }
  await m.produceAll([]);
  for(const seat of m.players.map(p=>p.seat)) {
   const yields=m.matchMetrics.projectProduction.filter(x=>x.seat===seat);
   assert.deepEqual(yields.map(x=>[x.project,x.resource,x.nominal]).sort(),[['mega_cluster','compute',2],['quantum','capability',1]]);
  }
 }
});

test('unaffordable, rival-host and stale host plans reject before any payment',async()=>{
 for(const resource of ['runway','compute']) {
  const m=await setup();m.round=4;m.players[0][resource]=resource==='runway'?2:0;
  for(const id of ['mega_cluster','fusion_demonstrator','quantum'])assert.equal(choices(m,0,id).length,0);
 }
 const m=await setup();m.round=4;const p=m.players[0];
 const plan=alone(m,0,'fusion_demonstrator');const own=p.facilities[0];
 assert.ok(!choices(m,0,'fusion_demonstrator').some(c=>c.parameters.project.hostId===m.players[1].facilities[0].id));
 p.facilities=[];const before=[p.runway,p.compute,p.scrutiny];
 assert.throws(()=>m.applyBuild(0,plan),/no longer legal/);assert.deepEqual([p.runway,p.compute,p.scrutiny],before);
 p.facilities=[own];const forged=structuredClone(plan);forged.parameters.project.hostId='rival';forged.parameters.actualRunwayCost=0;
 m.applyBuild(0,forged);assert.equal(p.projects[0].hostId,own.id);assert.equal(p.runway,9);
});

test('Build can construct the connected host and attach any personal project in the same action',async()=>{
 for(const id of ['mega_cluster','fusion_demonstrator','quantum']) {
  const m=await setup();m.round=4;const p=m.players[0];p.facilities=[];
  const plan=choices(m,0,id).find(c=>c.parameters.facility);assert.ok(plan);
  m.applyBuild(0,plan);assert.equal(p.facilities.length,1);assert.equal(p.projects[0].hostId,p.facilities[0].id);
  assert.equal(p.runway,12-plan.parameters.actualRunwayCost);
 }
});

test('Fusion follows its host, powers itself and only owned nearby Facilities, and uses no Generator slot',async()=>{
 const m=await setup();m.round=3;const p=m.players[0];const tile=m.board.find(t=>t.instanceId===p.facilities[0].tileId);
 const neighbor=m.board.find(t=>t.category!=='frontier'&&m.areAdjacent(tile.instanceId,t.instanceId));
 p.facilities.push({id:'s0-facility-2',tileId:neighbor.instanceId,category:neighbor.category});
 m.applyBuild(0,alone(m,0,'fusion_demonstrator'));
 assert.equal(m.latestPoweredFacilities(p).length,2);assert.equal(p.generators.length,0);
 const distant=m.board.find(t=>t.category!=='frontier'&&t.instanceId!==neighbor.instanceId&&!m.areAdjacent(t.instanceId,neighbor.instanceId));
 const occupiedBefore=m.generatorOccupancy(tile.instanceId);
 p.facilities[0].tileId=distant.instanceId;p.facilities[0].category=distant.category;
 assert.equal(m.generatorOccupancy(tile.instanceId),occupiedBefore);
 assert.deepEqual([...m.infrastructureState(p).locallyEligible],[p.facilities[0].id]);
 const rival=m.players[1];rival.facilities.push({id:'rival-second',tileId:distant.instanceId,category:distant.category});
 assert.ok(!m.infrastructureState(rival).locallyEligible.has('rival-second'));
});

test('host outages pause yields without resetting chips; Quantum caps and thresholds apply at Production',async()=>{
 const m=await setup();m.round=4;const p=m.players[0];
 const tile=m.board.find(t=>t.instanceId===p.facilities[0].tileId);
 const second=m.board.find(t=>t.category==='cloud'&&t.instanceId!==tile.instanceId)||m.board.find(t=>t.instanceId!==tile.instanceId&&t.category!=='frontier');
 p.facilities.push({id:'s0-facility-2',tileId:second.instanceId,category:second.category});
 p.generators=[{id:'ordinary',tileId:second.instanceId,sourceId:'clean_infrastructure'}];
 for(const id of ['mega_cluster','quantum'])m.applyBuild(0,choices(m,0,id).find(c=>!c.parameters.facility&&c.parameters.project.hostId==='s0-facility-2'));
 p.capability=8;m.synchronizePublicMandate(p,'fixture');const score=p.mandate;
 p.generators=[];await m.produceAll([]);assert.equal(p.capability,8);assert.equal(m.matchMetrics.projectProduction.filter(x=>x.seat===0).length,0);
 p.generators=[{id:'ordinary',tileId:second.instanceId,sourceId:'clean_infrastructure'}];
 await m.produceAll([]);assert.equal(p.capability,9);assert.ok(p.mandate>score);
 p.capability=12;await m.produceAll([]);assert.equal(p.capability,12);
 const projects=structuredClone(p.projects);p.scrutiny=0;await m.audit([]);assert.deepEqual(p.projects,projects);
});

test('Trust milestone and objective records use existing scoring history without handwriting',async()=>{
 const m=await setup();const p=m.players[0];
 assert.equal(m.highestTrustMilestone(p),Math.max(0,...m.config.scoring.trustThresholds.filter(t=>p.trust>=t.value).map(t=>t.value)));
 m.addResource(p,'trust',6);const high=m.highestTrustMilestone(p);const score=p.mandate;
 m.addResource(p,'trust',-2);m.addResource(p,'trust',2);assert.equal(p.mandate,score);assert.equal(m.highestTrustMilestone(p),high);
 m.roundMandate=m.mandateDocument.mandates.find(x=>x.id==='markets_prefer_destiny');p.roundMetrics.fundRunway=7;
 assert.deepEqual(m.objectiveRecord(p),{kind:'Runway gained through Fund',value:7});
 assert.deepEqual(m.snapshot().players[0].objectiveRecord,m.objectiveRecord(p));
 m.roundMandate=m.mandateDocument.mandates.find(x=>x.id==='building_has_weather');assert.equal(m.objectiveRecord(p),null);
});
