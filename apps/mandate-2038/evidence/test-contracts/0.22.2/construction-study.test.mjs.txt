import test from "node:test";
import assert from "node:assert/strict";
import { createInteractiveGame } from "../lab/runtime/create-interactive-game.js";
import { loadPlayerProfiles } from "../lab/personas/player-profile.js";
import { WeightedPlayerPolicy } from "../lab/policies/weighted-policy.js";

test("the deliberate infrastructure plan funds, connects hosts, and selects a legal project", async () => {
  const { match } = await createInteractiveGame({ playerCount: 4, seed: "construction-policy-contract" }, () => {});
  match.choose = async (_policies, _seat, _stage, choices) => choices.at(-1);
  await match.beginRound([]);
  const profiles = await loadPlayerProfiles();
  const policy = new WeightedPlayerPolicy(profiles.find(profile => profile.id === "infrastructure_compounder"),
    { selection: "greedy", treatment: "infrastructure_plan_v1" });
  const choose = choices => policy.rank(match.packet(0, "study", choices))[0].decision;
  const player = match.players[0];
  player.runway = 6;
  const first = choose(match.legalResolutions(0, "build"));
  assert.ok(["cloud", "chip", "research"].includes(first.parameters.destinationCategory));
  match.applyResolution(0, first);
  match.round = 2; await match.beginRound([]);
  player.runway = 1;
  assert.equal(choose(match.legalActionSelections(0)).actionId, "fund");
  player.runway = 4;
  const hosts = choose(match.legalResolutions(0, "build"));
  assert.equal(hosts.parameters.facility, true);
  assert.equal(hosts.parameters.project.id, "generator");
  match.applyResolution(0, hosts);
  assert.equal(match.latestPoweredFacilities(player).length, 2);
  match.round = 3; await match.beginRound([]);
  player.runway = 3; player.compute = 2;
  const cluster = choose(match.legalResolutions(0, "build"));
  assert.equal(cluster.parameters.project.id, "mega_cluster");
  assert.equal(cluster.parameters.facility, false);
  match.applyResolution(0, cluster);
  await match.produceAll([]);
  assert.deepEqual(match.matchMetrics.projectProduction.map(event => [event.round, event.seat, event.nominal]), [[3, 0, 2]]);
  assert.ok(match.matchMetrics.projectProduction[0].gained <= 2);
  // An existing project that loses its host must not count as productive.
  player.facilities = [];
  match.round = 4;
  await match.produceAll([]);
  assert.equal(match.matchMetrics.projectProduction.length, 1);
});

test('personal infrastructure treatment targets each unlock and reads the public price', async () => {
 const {match}=await createInteractiveGame({playerCount:4,seed:'personal-policy-contract'},()=>{});
 await match.beginRound([]);
 const profiles=await loadPlayerProfiles();const policy=new WeightedPlayerPolicy(profiles.find(p=>p.id==='infrastructure_compounder'),{selection:'greedy',treatment:'personal_infrastructure_v1'});
 const p=match.players[0];p.runway=12;p.compute=10;
 const choose=choices=>policy.rank(match.packet(0,'study',choices))[0].decision;
 match.applyResolution(0,choose(match.legalResolutions(0,'build')));
 for(const [era,id] of [[2,'mega_cluster'],[3,'fusion_demonstrator'],[4,'quantum']]) {
  match.round=era;await match.beginRound([]);p.runway=12;p.compute=10;
  const decision=choose(match.legalResolutions(0,'build'));
  assert.equal(decision.parameters.project?.id,id);
  if(id==='fusion_demonstrator')assert.equal(decision.parameters.facility,true);
  match.applyResolution(0,decision);
 }
 assert.equal(p.projects.length,3);
 assert.ok(p.facilities.length>=2);
 const packet=match.packet(0,'study',match.legalActionSelections(0));
 assert.deepEqual(packet.observation.personalProjectRules.cost,match.projectDocument.constructionCost);
});

test('study checkpoints verify both artifacts and reject duplicates, tampering and completed runs', async () => {
 const {loadCheckpoint}=await import('../lab/cli/construction-study.mjs');
 const {mkdtemp,mkdir,writeFile,rm}=await import('node:fs/promises');const {tmpdir}=await import('node:os');const {join}=await import('node:path');const {createHash}=await import('node:crypto');
 const root=await mkdtemp(join(tmpdir(),'mandate-checkpoint-'));
 try {
  const folder=join(root,'evidence/studies/simulation');await mkdir(folder,{recursive:true});
  const row={block:0,treatment:'personal_infrastructure_v1'};
  for(const key of ['report','outcomes']) {row[key]=`evidence/studies/simulation/${key}.json`;const bytes='{}\n';await writeFile(join(root,row[key]),bytes);row[`${key}Sha256`]=`sha256:${createHash('sha256').update(bytes).digest('hex')}`;}
  const path=join(folder,'checkpoint.json');const checkpoint={mode:'personal',seed:'fixture',complete:false,results:[row]};const args={root,mode:'personal',seed:'fixture'};
  await writeFile(path,JSON.stringify(checkpoint));assert.deepEqual((await loadCheckpoint(path,args)).results,[row]);
  await writeFile(join(root,row.outcomes),'changed');await assert.rejects(()=>loadCheckpoint(path,args),/hash mismatch/);await writeFile(join(root,row.outcomes),'{}\n');
  await writeFile(path,JSON.stringify({...checkpoint,results:[row,row]}));await assert.rejects(()=>loadCheckpoint(path,args),/Duplicate/);
  await writeFile(path,JSON.stringify({...checkpoint,complete:true}));await assert.rejects(()=>loadCheckpoint(path,args),/completed/);
 } finally {await rm(root,{recursive:true,force:true});}
});
