import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import { createInteractiveGame } from '../lab/runtime/create-interactive-game.js';
import { SpatialStudyPolicy, bundle, publicPower, spatialFeatures, rankLocations } from '../evidence/studies/2026-10-09-spatial-counterplay-policy.mjs';
import { pairedInterval } from '../evidence/studies/2026-10-09-spatial-counterplay.mjs';

const profiles = JSON.parse(await readFile(new URL('../dist/runtime/player-strategies.json', import.meta.url))).profiles;

test('paired uncertainty remains bounded and rejects invalid win-credit effects',()=>{
  const bound=pairedInterval(Array(192).fill(.1));assert.ok(Math.abs(bound.mean-.1)<1e-12);
  assert.ok(bound.lower<0&&bound.upper>.1,'small estimated gains do not pass with insufficient precision');
  assert.throws(()=>pairedInterval([2]),/registered support/);
  assert.deepEqual(pairedInterval([]),{n:0,mean:null,lower:-1,upper:1});
});
async function fixture() {
  const {match:m} = await createInteractiveGame({playerCount:4,seed:'spatial-contract-fixture'});
  m.round=3;for(const p of m.players)Object.assign(p,{runway:12,compute:12});
  return m;
}

test('public spatial predictor matches engine power after actual legal construction',async()=>{
  const withHosts=async()=>{
    const m=await fixture();const cloud=m.board.find(t=>t.category==='cloud');
    const far=m.board.find(t=>t.category==='government'&&!m.areAdjacent(t.instanceId,cloud.instanceId));
    m.players[0].facilities=[{id:'s0-facility-1',tileId:cloud.instanceId,category:cloud.category},
      {id:'s0-facility-2',tileId:far.instanceId,category:far.category}];return m;
  };
  const original = await withHosts();const choices=original.legalResolutions(0,'build');
  let newlyConnected=0;
  for(const choice of choices.filter(d=>d.parameters.facility || d.parameters.project?.id==='generator')) {
    const m=await withHosts();const packet=m.packet(0,'resolve',m.legalResolutions(0,'build'));
    const expected=spatialFeatures(packet,choice).power;
    const before=m.infrastructureState(m.players[0]).locallyEligible.size;
    m.applyBuild(0,choice);
    assert.equal(m.infrastructureState(m.players[0]).locallyEligible.size-before,expected);
    newlyConnected+=expected>0?1:0;
    const publicPlayer=m.publicObservation(0).publicTable.players[0];
    assert.deepEqual([...publicPower(m.publicObservation(0).board,publicPlayer)], [...m.infrastructureState(m.players[0]).locallyEligible]);
  }
  assert.ok(newlyConnected>0,'exercise sources that connect previously offline infrastructure');
});

test('rival filling the last Facility slot removes the preferred location through actual legality',async()=>{
  const m=await fixture();const clouds=m.board.filter(t=>t.category==='cloud');
  m.players[1].facilities=[{id:'s1-facility-1',tileId:clouds[0].instanceId,category:'cloud'}];
  const choices=m.legalResolutions(0,'build').filter(d=>d.parameters.facility&&!d.parameters.project);
  const packet=m.packet(0,'resolve',choices);const before=structuredClone(packet);
  const ranked=rankLocations(packet,choices,'compute');assert.deepEqual(packet,before);
  const destination=ranked[0].decision.parameters.destinationId;
  const existing=m.players[1].facilities[0];existing.tileId=destination;existing.category=m.board.find(t=>t.instanceId===destination).category;
  const rival=m.legalResolutions(1,'build').find(d=>d.parameters.facility&&!d.parameters.project&&d.parameters.destinationId===destination);
  assert.ok(rival);m.applyBuild(1,rival);
  const after=m.legalResolutions(0,'build').filter(d=>d.parameters.facility&&!d.parameters.project);
  assert.ok(!after.some(d=>d.parameters.destinationId===destination));
  assert.notEqual(rankLocations(m.packet(0,'resolve',after),after,'compute')[0].decision.parameters.destinationId,destination);
});

test('diagnostic policy changes only legal location choices in the ordinary action bundle',async()=>{
  const m=await fixture();const choices=m.legalResolutions(0,'build');const packet=m.packet(0,'resolve',choices);
  const baseline=new SpatialStudyPolicy(profiles[0],'greedy');const treatment=new SpatialStudyPolicy(profiles[0],'greedy',{plan:'power'});
  const a=await baseline.decide(packet), b=await treatment.decide(packet);
  const find=response=>choices.find(d=>d.decisionId===response.decision.decisionId);
  assert.equal(bundle(find(a)),bundle(find(b)));
  assert.deepEqual(await treatment.decide(packet),b);
});

async function ventureFixture() {
  const m=await fixture();const left=m.board.find(t=>t.category==='cloud');const right=m.board.find(t=>t.category==='capital'&&m.areAdjacent(left.instanceId,t.instanceId)) || m.board.find(t=>t.category!=='frontier'&&m.areAdjacent(left.instanceId,t.instanceId));
  for(const [seat,tile] of [left,right].entries())m.players[seat].facilities=[{id:`s${seat}-facility-1`,tileId:tile.instanceId,category:tile.category}];
  const decision=m.legalResolutions(0,'influence').find(d=>d.parameters.mode==='joint_venture'&&d.parameters.targetSeat===1);
  assert.ok(decision);return {m,decision,left,right};
}

test('Venture responder receives exact public proposer, hosts, connection status and income; rejection clears proposal',async()=>{
  const {m,decision,left,right}=await ventureFixture();let observed;
  const policies=m.players.map(()=>({decide:async packet=>{
    observed=packet.observation.publicTable.pendingJointVenture;
    assert.equal(packet.seat,1);assert.equal(observed.proposerSeat,0);
    assert.equal(observed.left.tileId,left.instanceId);assert.equal(observed.right.tileId,right.instanceId);
    assert.equal(observed.left.powered,true);assert.equal(observed.right.powered,true);
    assert.equal(observed.income.find(p=>p.seat===1).resource,'compute');
    assert.equal(packet.observation.publicTable.players[0].facilities[0].id,observed.left.facilityId);
    assert.equal(packet.observation.trainingDeck,undefined);
    return {decision:{decisionId:'agreement_reject'},receipt:{provider:'test'}};
  }}));
  assert.equal(await m.negotiate(policies,0,decision),false);assert.ok(observed);
  assert.equal(m.contracts.length,0);assert.equal(m.publicObservation(1).publicTable.pendingJointVenture,null);
});

test('Venture terms clear on acceptance and policy failure; information alone changes no contract rules',async()=>{
  for(const fail of [false,true]) {
    const {m,decision}=await ventureFixture();const policies=m.players.map(()=>({decide:async()=>{
      if(fail)throw new Error('test responder failure');
      return {decision:{decisionId:'agreement_accept'},receipt:{provider:'test'}};
    }}));
    if(fail)await assert.rejects(()=>m.negotiate(policies,0,decision),/test responder failure/);
    else {assert.equal(await m.negotiate(policies,0,decision),true);assert.equal(m.contracts.length,1);}
    assert.equal(m.publicObservation(1).publicTable.pendingJointVenture,null);
  }
});

test('offer-aware counter uses the actual proposer score, not hidden state or inferred seat identity',async()=>{
  const {m,decision}=await ventureFixture();m.players[0].mandate=20;
  const policies=profiles.slice(0,4).map(p=>new SpatialStudyPolicy(p,'greedy',{plan:'refusal'}));
  assert.equal(await m.negotiate(policies,0,decision),false);assert.equal(m.contracts.length,0);
});
