import test from 'node:test';
import assert from 'node:assert/strict';
import {WeightedPlayerPolicy} from '../lab/policies/weighted-policy.js';
import {fixture,profiles} from './helpers/smaller-game.mjs';

for(const selection of ['greedy','weighted'])test(`${selection} does not waste a turn on an unaffordable Action when another resolves`,async()=>{
 const m=fixture(),p=m.players[0];p.compute=0;p.runway=0;
 const profile=structuredClone(profiles[0]);profile.strategy.actionWeights.research=1e9;
 const policy=new WeightedPlayerPolicy(profile,{selection});
 const packet=m.packet(0,'select',m.legalActionSelections(0));
 assert.ok(packet.legalDecisions.some(d=>d.actionId==='research'&&!d.consequences.resolvableWithoutTrade));
 const reply=await policy.decide(packet);
 assert.equal(packet.legalDecisions.find(d=>d.decisionId===reply.decision.decisionId).consequences.resolvableWithoutTrade,true);
});
test('genuinely stranded positions retain explicit blocked-turn choices',async()=>{
 const m=fixture(),p=m.players[0];p.compute=0;p.runway=0;p.pieces.forEach(o=>o.tileId='research-3');
 const packet=m.packet(0,'select',m.legalActionSelections(0));
 assert.ok(packet.legalDecisions.every(d=>!d.consequences.resolvableWithoutTrade));
 const policy=new WeightedPlayerPolicy(profiles[0]);
 assert.equal(policy.rank(packet).length,packet.legalDecisions.length);
 const reply=await policy.decide(packet);assert.ok(packet.legalDecisions.some(d=>d.decisionId===reply.decision.decisionId));
});
