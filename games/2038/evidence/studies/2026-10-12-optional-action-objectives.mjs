import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {resolve, join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {isDeepStrictEqual} from 'node:util';

const args=Object.fromEntries(process.argv.slice(2).map(x=>{const i=x.indexOf('=');if(i<1)throw new Error(`Expected key=value: ${x}`);return [x.slice(0,i),x.slice(i+1)];}));
const baseline=resolve(args.baseline), candidate=resolve(args.candidate), out=resolve(args.output);
const count=Number(args.players), backend=args.backend;
if(![3,4,5].includes(count)||!['greedy','weighted'].includes(backend))throw new Error('Invalid cohort');
const rootSeed='mandate-20261012-optional-action-objectives-v1';
const sha256=b=>createHash('sha256').update(b).digest('hex');
const load=(root,p)=>import(pathToFileURL(join(root,p)).href);
const [{SelectedRulesMatch:Baseline},{SelectedRulesMatch:Candidate}, {createPlayerPolicy}, {createPlayerPolicy:oldPolicy}, rng, versioning]=await Promise.all([
 load(baseline,'lab/environment/selected-rules-match.js'), load(candidate,'lab/environment/selected-rules-match.js'),
 load(candidate,'lab/policies/policy-factory.js'),load(baseline,'lab/policies/policy-factory.js'),
 load(baseline,'web/src/engine.js'),load(candidate,'lab/versioning/game-identity.js')]);
const input=Object.fromEntries(await Promise.all(['game-config','factions','headlines','projects','mandates','player-strategies'].map(async n=>[n,JSON.parse(await readFile(join(baseline,`dist/runtime/${n}.json`)))])));
const profiles=input['player-strategies'].profiles;
const resources=Object.keys(input['game-config'].resources);
const rotate=(arr,n)=>arr.map((_,i)=>arr[(i+n)%arr.length]);
class ObjectivesOnly extends Baseline {
 constructor(options){super(options);this.studyEarlyObjectives=Array.from({length:4},(_,i)=>{const pool=this.mandateDocument.mandates.filter(m=>m.era===i+1);return (this.mandateMode==='fixed'?pool:rng.shuffle(pool,rng.createRng(`${this.seed}:mandates:${i+1}`)))[0];});this.revealedMandates=[...this.studyEarlyObjectives];this.roundMandate=this.studyEarlyObjectives[0]||null;}
 async beginRound(){await Baseline.prototype.beginRound.call(this);this.revealedMandates=[...this.studyEarlyObjectives];}
}
class OptionalActionOnly extends Candidate {
 constructor(options){super(options);this.revealedMandates=[];this.roundMandate=null;}
 async beginRound(){await Baseline.prototype.beginRound.call(this);}
}
const arms={baseline_0_24_4:Baseline,objectives_only:ObjectivesOnly,optional_action_only:OptionalActionOnly,combined_candidate:Candidate};
function invariant(ok,msg){if(!ok)throw new Error(msg);}
function compact(result,match,production,choices){
 const objectiveCards=match.finalObjectives();
 const players=result.standings.map(p=>{
  const scoring=match.config.scoring;
  const scoreParts={capability:p.capability*scoring.capability,customers:p.customers*match.rulesVariant.customerPoints,reputation:p.reputation*scoring.reputation,agi:p.agiDeclared?scoring.agi:0,objectives:objectiveCards.reduce((n,c)=>n+c.standings.find(r=>r.seat===p.seat).points,0)};
  invariant(Object.values(scoreParts).reduce((a,b)=>a+b,0)===p.score,'Final score reconstruction failed');
  const turns=p.metrics.turns??Object.values(p.metrics.actions).reduce((a,b)=>a+b,0);
  invariant(turns===12,`Expected twelve turns, got ${turns}`);
  for(const k of resources){const def=match.config.resources[k];invariant(Number.isFinite(p[k])&&p[k]>=def.min&&p[k]<=def.cap,`Resource out of bounds: ${k}`);}
  return {seat:p.seat,factionId:p.factionId,profileId:p.profileId,backendId:p.backendId,score:p.score,scoreParts,...Object.fromEntries(resources.map(k=>[k,p[k]])),orgs:p.pieces.length,equipped:p.equippedOrgs,agiDeclared:p.agiDeclared,actions:p.metrics.actions,turns,forcedNoOps:p.metrics.forcedNoOps,blockedAfterCommitment:p.metrics.blockedAfterCommitment,policyFallbacks:p.metrics.policyFallbacks,skippedActions:choices.filter(c=>c.seat===p.seat&&c.skip).length,skippedActionCounts:p.metrics.skippedActions||{},deliberateSkips:p.metrics.deliberateSkips||0,selectedDestinations:Object.fromEntries([...new Set(choices.filter(c=>c.seat===p.seat&&c.stage==='select').map(c=>c.actionId))].map(a=>[a,choices.filter(c=>c.seat===p.seat&&c.stage==='select'&&c.actionId===a).length])),pieces:p.pieces};
 }).sort((a,b)=>a.seat-b.seat);
 invariant(match.complete&&match.round===4&&production.length===4&&objectiveCards.length===4,'Game did not complete four Eras/Productions/objectives');
 invariant(result.futureTimeline.length===12,'Wrong number of Headlines');
 return {complete:match.complete,winnerSeats:result.winnerSeats,worldEnding:result.worldEnding,players,objectives:objectiveCards,production,choices:choices.filter(c=>['select','resolve'].includes(c.stage)),tradeCounts:result.matchMetrics.trades};
}
async function play(Engine,block,{policyFactory=createPlayerPolicy,projection='batch'}={}){
 const roster=block.profileIds.map(id=>profiles.find(p=>p.id===id));
 const match=new Engine({config:input['game-config'],factions:block.factionIds.map(id=>input.factions.factions.find(f=>f.id===id)),profiles:roster,backends:roster.map(()=>backend),headlines:input.headlines,projects:input.projects,mandates:input.mandates,seed:block.seed,playerCount:count,mandateMode:block.mode,projection,recordReplay:false});
 const initialVisibleObjectiveCount=match.revealedMandates.length;
 const production=[],choices=[];
 const produce=match.produceAll.bind(match);
 match.produceAll=async function(){
  const rows=match.players.map(p=>{
   const before=Object.fromEntries(resources.map(k=>[k,p[k]]));const gross=Object.fromEntries(resources.map(k=>[k,0]));
   for(const org of p.pieces){const t=match.board.find(t=>t.instanceId===org.tileId);if(t)gross[t.yield.resource]+=t.yield.amount*(org.equipped?2:1);}
   gross.runway+=p.customers;
   if(match.hasFactionAbility(p,'the_shovels'))gross.runway+=Math.min(2,match.players.filter(x=>x.seat!==p.seat&&x.pieces.some(o=>o.equipped)).length);
   return {seat:p.seat,before,gross,orgs:p.pieces.length,equipped:p.pieces.filter(o=>o.equipped).length};
  });
  await produce();
  for(const row of rows){const p=match.players[row.seat];row.after=Object.fromEntries(resources.map(k=>[k,p[k]]));row.realized=Object.fromEntries(resources.map(k=>[k,p[k]-row.before[k]]));row.clipped=Object.fromEntries(resources.map(k=>[k,row.gross[k]-row.realized[k]]));for(const k of resources)invariant(row.realized[k]===Math.min(row.gross[k],match.config.resources[k].cap-row.before[k]),`Production mismatch: ${k}`);}
  production.push({era:match.round,players:rows});
 };
 const choose=match.choose.bind(match);
 match.choose=async function(policies,seat,stage,decisions){const decision=await choose(policies,seat,stage,decisions);choices.push({era:match.round,cycle:match.cycle,seat,stage,id:decision.decisionId,actionId:decision.actionId,parameters:decision.parameters,skip:Boolean(decision.parameters?.skipAction||decision.parameters?.skip||decision.parameters?.mode==='skip'||decision.decisionId.startsWith('skip_'))});return decision;};
 const policies=roster.map(p=>policyFactory(p,backend,{rosterProfileIds:roster.map(p=>p.id)}));
 const result=await match.play(policies);
 return {initialVisibleObjectiveCount,...compact(result,match,production,choices)};
}
function finalComparable(row){const {initialVisibleObjectiveCount,...rest}=row;return rest;}
function scenarios(smoke=false){const rows=[];for(const mode of ['fixed','variable'])for(const field of ['mixed_authored','identical_balanced'])for(let factionStart=0;factionStart<6;factionStart++)for(let seatRotation=0;seatRotation<count;seatRotation++){
 const factionWindow=Array.from({length:count},(_,i)=>input.factions.factions[(factionStart+i)%6].id);
 const factionIds=rotate(factionWindow,seatRotation);
 const profileStart=(factionStart+6*seatRotation)%profiles.length;
 const profileIds=Array.from({length:count},(_,i)=>field==='identical_balanced'?'balanced_operator':profiles[(profileStart+i)%profiles.length].id);
 rows.push({count,backend,mode,field,factionStart,seatRotation,factionIds,profileIds,seed:`${rootSeed}:${smoke?'smoke':'comparison'}:${count}:${backend}:${mode}:${field}:${factionStart}:${seatRotation}`});if(smoke&&rows.length===2)return rows;
 }return rows;}
const identityOptions={profiles,backends:[backend],policyProjection:'batch',experimentKind:'optional_action_public_objectives_diagnostic'};
const identities={baseline:await versioning.loadGameIdentity({...identityOptions,root:baseline}),candidate:await versioning.loadGameIdentity({...identityOptions,root:candidate})};
const files=['lab/environment/selected-rules-match.js','lab/policies/weighted-policy.js','dist/runtime/game-config.json','dist/runtime/player-strategies.json'];
const fileHashes={};for(const [label,root] of [['baseline',baseline],['candidate',candidate]])fileHashes[label]=Object.fromEntries(await Promise.all(files.map(async f=>[f,sha256(await readFile(join(root,f)))])));
const inputHashes=Object.fromEntries(await Promise.all(Object.keys(input).map(async n=>[n,sha256(await readFile(join(baseline,`dist/runtime/${n}.json`)))])));
const report={inputHashes,studyId:'2026-10-12-optional-action-public-objectives-v1',evidenceType:'simulation',status:'running',sourceCommit:'aba758ac6f4b6eb597856c553d91d3d157d9e884',runtime:process.version,count,backend,rootSeed,identities,fileHashes,runnerSha256:sha256(await readFile(new URL(import.meta.url))),controls:[],rows:[]};
await mkdir(resolve(out,'..'),{recursive:true});await writeFile(out,JSON.stringify({status:'running',count,backend})+'\n',{flag:'wx'});
try{
 for(const block of scenarios(true)){
  const before=await play(Baseline,block,{policyFactory:oldPolicy}),after=await play(Baseline,block);
  invariant(isDeepStrictEqual(before,after),'Candidate policy changed original baseline');
  const batch=await play(Candidate,block),rich=await play(Candidate,block,{projection:'rich'});
  invariant(isDeepStrictEqual(batch,rich),'Candidate rich/batch outcome mismatch');
  report.controls.push({block,baselinePolicyParity:true,candidateRichBatchParity:true,baselineOutcome:before,candidateOutcome:batch});
 }
 for(const block of (args.smoke==='true'?[]:scenarios())){
  const outcomes={};for(const [name,Engine] of Object.entries(arms))outcomes[name]=await play(Engine,block);
  invariant(outcomes.baseline_0_24_4.initialVisibleObjectiveCount===0&&outcomes.optional_action_only.initialVisibleObjectiveCount===0&&outcomes.objectives_only.initialVisibleObjectiveCount===4&&outcomes.combined_candidate.initialVisibleObjectiveCount===4,'Unexpected setup objective visibility');
  invariant(isDeepStrictEqual(finalComparable(outcomes.baseline_0_24_4),finalComparable(outcomes.objectives_only)),'Objective-only arm changed objective-ignorant policy outcomes');
  invariant(isDeepStrictEqual(finalComparable(outcomes.optional_action_only),finalComparable(outcomes.combined_candidate)),'Visibility changed optional-action policy outcomes');
  report.rows.push({block,arms:outcomes});if(report.rows.length%12===0)process.stderr.write(`${count}/${backend} ${report.rows.length}/${scenarios().length}\n`);
 }
 for(const [label,root] of [['baseline',baseline],['candidate',candidate]])for(const f of files)invariant(fileHashes[label][f]===sha256(await readFile(join(root,f))),'Source drift');
 report.status='complete';
}catch(e){report.status='failed';report.error=String(e.stack);throw e;}
finally{await writeFile(out,JSON.stringify(report)+'\n');}
console.log(JSON.stringify({output:out,count,backend,scenarios:report.rows.length,comparisonGames:report.rows.length*4,controlGames:report.controls.length*4,status:report.status,sha256:sha256(await readFile(out))}));
