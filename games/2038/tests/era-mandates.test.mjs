import assert from 'node:assert/strict';
import test from 'node:test';
import { readFile } from 'node:fs/promises';
import { createInteractiveGame } from '../lab/runtime/create-interactive-game.js';
import { evaluateEraMandate, activeJointVenture, nominalComputeCapacity } from '../lab/rules/era-mandates.js';
const cards = JSON.parse(await readFile(new URL('../dist/runtime/mandates.json', import.meta.url))).mandates;
const card = id => cards.find(c => c.id === id);
const board = [{instanceId:'a',id:'cloud',category:'cloud',q:0,r:0}, {instanceId:'b',id:'chip',category:'chip',q:1,r:0}, {instanceId:'c',id:'grid_reactor',category:'energy',q:4,r:0}];
function player(seat, tileId = seat ? 'b' : 'a') {
  return {seat, runway:4, compute:12, capability:3, trust:4, customers:3, scrutiny:0, pieces:[{tileId}], generators:[], projects:[], facilities:[{id:`s${seat}-f1`,tileId,category:board.find(t=>t.instanceId===tileId).category}], history:{},roundMetrics:{}};
}
function state() {return {board:structuredClone(board),players:[player(0),player(1)],contracts:[],projectDocument:{projects:[{id:'mega_cluster',production:{resource:'compute',amount:2}}]}};}
const evaluate = (id,s,p=s.players[0]) => evaluateEraMandate(card(id),s,p);

test('all twelve authored definitions evaluate explicit current metrics without mutation',()=>{
 const s=state();s.players[0].projects=[{projectId:'mega_cluster',hostId:'s0-f1'}];
 s.contracts=[{id:1,kind:'joint_venture',left:{seat:0,facilityId:'s0-f1'},right:{seat:1,facilityId:'s1-f1'}}];
 const expected={quarter_humanity_notices:3,continent_signs_loi:3,building_has_weather:1,stack_reaches_horizon:2,voluntary_coordination_triumphs:1,legibility_offensive:4,national_champion_without_nationalization:1,model_ate_tuesday:3,compute_new_weather:5,zero_incident_quarter:0,responsible_acceleration:3,markets_prefer_destiny:4};
 const before=structuredClone(s);
 for(const c of cards) assert.deepEqual(evaluate(c.id,s),{qualified:true,value:expected[c.id],direction:c.id==='zero_incident_quarter'?'min':'max'},c.id);
 assert.deepEqual(s,before);assert.equal(cards.length,12);
 for(const c of cards) {assert.equal(c.record,undefined);assert.ok(c.rulesText.includes('after Audit'));}
});

test('no qualifiers score nothing; equal current state ignores every historical counter',()=>{
 const s=state();const empty={...player(0),runway:0,compute:0,capability:0,customers:0,trust:0,scrutiny:0,facilities:[],pieces:[]};s.players=[empty,{...structuredClone(empty),seat:1}];
 for(const c of cards) assert.equal(evaluateEraMandate(c,s,empty).qualified,false,c.id);
 const current=state();const before=cards.map(c=>evaluateEraMandate(c,current,current.players[0]));
 Object.assign(current.players[0],{history:{cumulativeScrutiny:999,agiClaimedRound:4},roundMetrics:{capabilityStart:99,customersStart:99,scrutinyStart:99,fundRunway:99,computeProduced:99,bestTrainingDomains:99,deployed:false,activeNewJointVentures:99},metrics:{scrutinyAdded:999},latestProductionSnapshot:{poweredFacilityIds:[]}});
 assert.deepEqual(cards.map(c=>evaluateEraMandate(c,current,current.players[0])),before);
});

test('zero values qualify by current Customer/Facility predicates, not generic positivity',()=>{
 const s=state();s.players[0].trust=0;s.players[0].runway=0;
 assert.equal(evaluate('legibility_offensive',s).qualified,true);
 assert.equal(evaluate('markets_prefer_destiny',s).qualified,true);
 assert.equal(evaluate('zero_incident_quarter',s).qualified,true);
 s.players[0].customers=0;
 assert.equal(evaluate('legibility_offensive',s).qualified,false);
 assert.equal(evaluate('zero_incident_quarter',s).qualified,false);
 s.players[0].trust=1;assert.equal(evaluate('model_ate_tuesday',s).qualified,false);
});

test('capacity and Venture eligibility follow current fixed hosts, adjacency and connections',()=>{
 const s=state();const p=s.players[0];p.facilities.push({id:'s0-f2',tileId:'c',category:'energy',customSilicon:true,powered:true});
 p.projects=[{projectId:'mega_cluster',hostId:'s0-f2',builtEra:2}];
 const contract={id:7,kind:'joint_venture',createdRound:0,left:{seat:0,facilityId:'s0-f1'},right:{seat:1,facilityId:'s1-f1'}};s.contracts=[contract];
 assert.equal(activeJointVenture(s,contract),true);assert.equal(nominalComputeCapacity(s,p),3);
 p.generators=[{tileId:'c'}];assert.equal(nominalComputeCapacity(s,p),7);
 p.generators=[];assert.equal(nominalComputeCapacity(s,p),3);
 s.players[1].facilities[0].tileId='c';assert.equal(activeJointVenture(s,contract),false);assert.equal(nominalComputeCapacity(s,p),2);
 s.players[1].facilities[0].tileId='b';contract.right.facilityId='wrong-owner';assert.equal(activeJointVenture(s,contract),false);
 contract.right.facilityId='s1-f1';s.contracts=[];assert.equal(evaluate('voluntary_coordination_triumphs',s).qualified,false);
});

test('engine scores max, min, ties and valid zero only after current qualification',async()=>{
 const {match:m}=await createInteractiveGame({playerCount:3,seed:'current-objective-boundaries'});
 for(const p of m.players)Object.assign(p,{customers:3,trust:2,capability:2,scrutiny:0});
 for(const id of ['quarter_humanity_notices','zero_incident_quarter']){
  m.roundMandate=card(id);const before=m.players.map(p=>p.mandate);m.scoreMandate();
  assert.deepEqual(m.players.map((p,i)=>p.mandate-before[i]),[1,1,1]);
 }
 m.roundMandate=card('zero_incident_quarter');m.players[1].scrutiny=1;m.players[2].customers=2;
 let before=m.players.map(p=>p.mandate);m.scoreMandate();assert.deepEqual(m.players.map((p,i)=>p.mandate-before[i]),[2,0,0]);
 for(const p of m.players)p.customers=0;before=m.players.map(p=>p.mandate);m.scoreMandate();assert.deepEqual(m.players.map(p=>p.mandate),before);
 assert.ok(m.matchMetrics.eraMandateScores.every(r=>r.standings.every(s=>typeof s.qualified==='boolean')));
});

test('ordinary Production shares capacity and active Ventures without double income',async()=>{
 const {match:m}=await createInteractiveGame({playerCount:2,seed:'capacity-production-shared'});await m.beginRound([]);
 const left=m.board.find(t=>t.category==='cloud');const right=m.board.find(t=>t.category==='chip'&&m.areAdjacent(left.instanceId,t.instanceId)) || m.board.find(t=>m.areAdjacent(left.instanceId,t.instanceId));
 for(const [i,t]of [left,right].entries())Object.assign(m.players[i],{compute:0,customers:0,facilities:[{id:`s${i}-f1`,tileId:t.instanceId,category:t.category,customSilicon:true}],projects:[]});
 m.contracts=[{id:1,kind:'joint_venture',createdRound:-4,left:{seat:0,facilityId:'s0-f1'},right:{seat:1,facilityId:'s1-f1'}}];
 m.choose=async(_p,_s,_stage,choices)=>choices[0];
 const expected=m.players.map(p=>nominalComputeCapacity(m,p));await m.produceAll([]);
 assert.deepEqual(m.players.map(p=>p.roundMetrics.computeProduced),expected);
 const before=structuredClone(m.players);m.roundMandate=card('compute_new_weather');
 for(let n=0;n<3;n++)for(const p of m.players)m.currentEraObjective(p);
 assert.deepEqual(m.players,before);
});

test('after-Audit standing includes penalties and AGI recognition, regardless of Deploy history',async()=>{
 const {match:m}=await createInteractiveGame({playerCount:2,seed:'audit-current-objectives'});await m.beginRound([]);
 const p=m.players[0];m.roundMandate=card('legibility_offensive');p.customers=1;p.trust=4;p.roundMetrics.deployed=false;
 assert.equal(m.currentEraObjective(p).qualified,true);p.agiDeclared=true;m.applyAutomaticPenalty(p,'player_audit');
 assert.equal(m.currentEraObjective(p).value,p.trust);assert.equal(p.agiDeclared,true);
});


test("settlement reads the table after Production, recognition and Audit in that order",async()=>{
 const {match:m}=await createInteractiveGame({playerCount:2,seed:'current-scoring-point'});m.round=4;
 m.roundMandate=card('zero_incident_quarter');
 const [p,q]=m.players;Object.assign(p,{customers:2,scrutiny:3});Object.assign(q,{customers:3,scrutiny:2});
 const phases=[];
 m.produceAll=async()=>{phases.push('production');p.customers=3;};
 m.declareAgiAchievements=async()=>{phases.push('recognition');p.agiDeclared=true;};
 m.audit=async()=>{phases.push('audit');p.scrutiny=0;};
 const original=m.scoreMandate.bind(m);m.scoreMandate=()=>{phases.push('scoring');assert.equal(p.agiDeclared,true);original();};
 await m.finishSelectedRound([]);
 assert.deepEqual(phases,['production','recognition','audit','scoring']);
 assert.deepEqual(m.matchMetrics.eraMandateScores.at(-1).standings.map(s=>s.points),[2,0]);
});
