import {readFile, writeFile, mkdir} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {classifyWinningPath} from '../../lab/balance/winning-path.js';
const baseline=process.argv[2];
if(!baseline)throw new Error('Pass the compiled frozen equipment-only baseline game directory.');
const roots=[resolve(baseline),process.cwd()];
if(execFileSync('git',['status','--porcelain','--','.'],{encoding:'utf8'}).trim())throw new Error('Candidate study requires clean committed sources.');
const sourceCommit=execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim();
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const lanes=[];
for(const root of roots){
 const {verifyRelease}=await import(pathToFileURL(`${root}/tasks/release-artifacts.mjs`));
 await verifyRelease(root);
 const pointer=JSON.parse(await readFile(`${root}/versions/current.json`));
 const manifest=JSON.parse(await readFile(`${root}/${pointer.manifest}`));
 const {SelectedRulesMatch}=await import(pathToFileURL(`${root}/lab/environment/selected-rules-match.js`));
 const {createPlayerPolicy}=await import(pathToFileURL(`${root}/lab/policies/policy-factory.js`));
 const files=['game-config','factions','headlines','projects','tactics','mandates','secret-objectives','player-strategies'];
 const bytes=await Promise.all(files.map(f=>readFile(`${root}/dist/runtime/${f}.json`)));
 const [config,factions,headlines,projects,tactics,mandates,objectives,profiles]=bytes.map(b=>JSON.parse(b));
 lanes.push({SelectedRulesMatch,createPlayerPolicy,config,factions:factions.factions,headlines,projects,tactics,mandates,objectives,profiles:profiles.profiles,
  releaseIdentity:{gameVersion:pointer.gameVersion,rulesVersion:pointer.rulesCandidate.version,engineFingerprint:manifest.engine.fingerprint,mechanicsFingerprint:pointer.mechanicsFingerprint},inputHashes:Object.fromEntries(files.map((f,i)=>[f,sha(bytes[i])])),policyHash:sha(await readFile(`${root}/lab/policies/weighted-policy.js`))});
}
if(lanes[0].policyHash!==lanes[1].policyHash)throw new Error('Policies changed between arms');
const pairs=[];
for(const count of [4,3,5])for(let faction=0;faction<6;faction++)for(let focalSeat=0;focalSeat<(count===4?4:1);focalSeat++)for(const backend of ['weighted','greedy'])for(let rotation=0;rotation<3;rotation++){
 const seed=`current-era-${count}-${faction}-${focalSeat}-${backend}-${rotation}`;
 const outcomes=[];
 for(const [arm,lane] of lanes.entries()){
  const factions=Array.from({length:count},(_,seat)=>lane.factions[(faction+seat-focalSeat+6)%6]);
  const profiles=Array.from({length:count},(_,seat)=>lane.profiles[(faction+seat)%lane.profiles.length]);
  const match=new lane.SelectedRulesMatch({...lane,factions,profiles,backends:Array(count).fill(backend),seed,playerCount:count,simulateNegotiation:true,recordReplay:false});
  for(const era of [1,2,3,4]){
   const deck=lane.mandates.mandates.filter(c=>c.era===era);
   match.mandateDeck[era]=deck[rotation];
  }
  const receipts=[];const score=match.scoreMandate.bind(match);
  match.scoreMandate=()=>{
   const card=match.roundMandate;const before=match.players.map(p=>p.mandate);
   const standings=match.players.map(p=>{
    if(arm===1)return {seat:p.seat,...match.currentEraObjective(p)};
    const value=match.mandateValue(p);const q=card.id==='zero_incident_quarter'?p.metrics.scrutinyAdded-p.roundMetrics.scrutinyStart:value;
    return {seat:p.seat,value,qualified:q>=(card.minimumQualification??1),direction:'max'};
   });
   score();receipts.push({round:match.round,id:card.id,standings:standings.map(s=>({...s,points:match.players[s.seat].mandate-before[s.seat]})),
    resources:match.players.map(p=>({seat:p.seat,factionId:p.factionId,customers:p.customers,runway:p.runway,trust:p.trust,capability:p.capability,scrutiny:p.scrutiny}))});
  };
  const policies=profiles.map(p=>lane.createPlayerPolicy(p,backend));
  const result=await match.play(policies);
  if(!match.complete || receipts.length!==4 || result.standings.length!==count || !result.standings.every(p=>Number.isFinite(p.score)))throw new Error('Incomplete match');
  outcomes.push({arm:arm?'candidate':'baseline',receipts,result,finalResources:match.players.map(p=>({seat:p.seat,runway:p.runway,customers:p.customers}))});
 }
 pairs.push({seed,playerCount:count,faction,focalSeat,backend,rotation,outcomes});
 if(pairs.length%24===0)process.stderr.write(`${pairs.length}/216 paired blocks complete\n`);
}
const archive='evidence/studies/simulation/2026-10-09-current-state-objectives-raw.json';
await mkdir(resolve(archive,'..'),{recursive:true});
const raw=JSON.stringify({evidenceType:'simulation',sourceCommit,baselineCommit:'daf5bbd14',pairs});await writeFile(archive,raw+'\n');
const summary={};
for(const arm of ['baseline','candidate']){
 const objectives={};const factions={};const paths={};const counts={};
 let repeats=0,repeatEligible=0;
 for(const pair of pairs){
  const o=pair.outcomes.find(o=>o.arm===arm);const count=pair.playerCount;
  const group=counts[count] ||= {games:0,score:0,runway:0,customers:0,players:0};group.games++;
  for(const p of o.result.standings){
   group.score+=p.score;group.runway+=o.finalResources.find(r=>r.seat===p.seat).runway;group.customers+=p.customers;group.players++;
   const k=`${count}p/${p.factionId}/seat${p.seat}`;const f=factions[k]||={games:0,wins:0,score:0};f.games++;f.wins+=o.result.winnerSeats.includes(p.seat)?1/o.result.winnerSeats.length:0;f.score+=p.score;
  }
  for(const p of o.result.standings.filter(p=>o.result.winnerSeats.includes(p.seat))){const label=classifyWinningPath(p);const k=typeof label==='string'?label:JSON.stringify(label);paths[k]=(paths[k]||0)+1;}
  for(const receipt of o.receipts){
   const key=`${count}p/${receipt.id}`;const r=objectives[key]||={games:0,qualified:0,opportunities:0,noQualifier:0,points:0,zeroWinners:0,factionPoints:{},seatPoints:{}};
   r.games++;r.noQualifier+=receipt.standings.some(s=>s.qualified)?0:1;
   for(const s of receipt.standings){r.opportunities++;r.qualified+=s.qualified?1:0;r.points+=s.points;r.zeroWinners+=s.points&&s.value===0?1:0;
    const faction=receipt.resources[s.seat].factionId;r.factionPoints[faction]=(r.factionPoints[faction]||0)+s.points;r.seatPoints[s.seat]=(r.seatPoints[s.seat]||0)+s.points;}
  }
  const early=o.receipts.find(r=>r.id==='quarter_humanity_notices');const late=o.receipts.find(r=>r.id==='continent_signs_loi');
  if(early&&late){repeatEligible++;repeats+=early.standings.some(e=>e.points>0&&late.standings.some(l=>l.seat===e.seat&&l.points>0))?1:0;}
 }
 summary[arm]={counts,objectives,factions,winningPaths:paths,repeatedCustomerWinnerGames:repeats,repeatedCustomerComparableGames:repeatEligible};
}
const deltas=pairs.map(p=>({seed:p.seed,playerCount:p.playerCount,scoreBySeat:p.outcomes[1].result.standings.map((s,i)=>({seat:s.seat,delta:s.score-p.outcomes[0].result.standings.find(b=>b.seat===s.seat).score}))}));
const receipt={date:'2026-10-09',evidenceType:'simulation',hypothesis:'Current-state objectives preserve completion while changing incentives; eligibility and concentration require fresh testing.',preregistration:'2026-10-09-current-state-objectives-preregistration.md',candidateSourceCommit:sourceCommit,baselineCommit:'daf5bbd14',candidateVersion:'0.22.1',rulesVersion:'0.12.0-rc.15-test',runCount:pairs.length*2,matchedPairs:pairs.length,backends:['weighted','greedy'],playerCounts:[4,3,5],profiles:'canonical profiles rotated identically',rulesVariant:'eight-card current-state package',auditedSurfaces:{rules:'current-state scoring after Audit; ordinary actions unchanged',components:'eight redesigned cards; objective cube removed',simulator:'pure evaluator and shared production predicate',browser:'current qualification/value and independent kits',referencePlayerAids:'current-state scoring reminder',tests:'all metrics, history independence, no-double-production, kit permutations',playtestDocumentation:'current-state and ownership observation checks',policies:'no change',costsAndFactionStarts:'no change'},archive,archiveSha256:sha(raw+'\n'),inputs:lanes.map(l=>({releaseIdentity:l.releaseIdentity,inputHashes:l.inputHashes,policyHash:l.policyHash})),summary,pairedScoreDeltas:deltas,limits:['No human playtest. No policy retuning. Package-level descriptive comparison; no isolated causal starting-value conclusion. No balance promotion. New thresholds remain hypotheses.']};
await writeFile(process.argv[3] || 'evidence/studies/2026-10-09-current-state-objectives-receipt.json',JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify({pairs:pairs.length,runs:pairs.length*2,archive,hash:receipt.archiveSha256}));
