import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { SelectedRulesMatch } from '../../lab/environment/selected-rules-match.js';
import { activeJointVenture } from '../../lab/rules/era-mandates.js';
import { loadGameIdentity } from '../../lab/versioning/game-identity.js';
import { canonicalRulesVariant } from '../../lab/environment/rules-variant.js';
import { verifyRelease } from '../../tasks/release-artifacts.mjs';
import { SpatialStudyPolicy, plans, distance } from './2026-10-09-spatial-counterplay-policy.mjs';

export const mean = xs => xs.reduce((s,x)=>s+x,0)/Math.max(1,xs.length);
export function pairedInterval(xs, { family = 8, alpha = .05, low = -1, high = 1 } = {}) {
  if(xs.some(x=>!Number.isFinite(x)||x<low||x>high))throw new Error('Paired effects exceed registered support');
  if (!xs.length) return { n:0, mean:null, lower:low, upper:high };
  const radius=(high-low)*Math.sqrt(Math.log(2*family/alpha)/(2*xs.length));
  return {n:xs.length,mean:mean(xs),lower:Math.max(low,mean(xs)-radius),upper:Math.min(high,mean(xs)+radius),method:'bounded Hoeffding, Bonferroni family alpha 0.05'};
}

export function scoreInterval(xs) {
  const average=mean(xs);const variance=xs.length>1?xs.reduce((s,x)=>s+(x-average)**2,0)/(xs.length-1):0;
  const radius=1.96*Math.sqrt(variance/Math.max(1,xs.length));
  return {n:xs.length,mean:average,lower:average-radius,upper:average+radius,method:'unadjusted normal approximation; descriptive only'};
}

function blocks(stage, counts, repetitions) {
  const result=[];
  for(const count of counts)for(let faction=0;faction<6;faction++)for(let seat=0;seat<count;seat++)for(const backend of ['weighted','greedy'])for(let repeat=0;repeat<repetitions;repeat++) {
    result.push({stage,count,faction,seat,backend,repeat,scaffold:Boolean((faction+seat+repeat)%2),
      counterSeat:(seat+1+(faction+repeat)%(count-1))%count,
      seed:`spatial-20261009-${stage}-${count}-${faction}-${seat}-${backend}-${repeat}`});
  }
  return result;
}

export async function runStudy({smoke=false}={}) {
  if(execFileSync('git',['status','--porcelain','--','.'],{encoding:'utf8'}).trim())throw new Error('Study requires clean committed source');
  await verifyRelease(process.cwd());
  const files=['game-config','factions','headlines','projects','tactics','mandates','secret-objectives','player-strategies'];
  const bytes=await Promise.all(files.map(f=>readFile(`dist/runtime/${f}.json`)));
  const [config,factions,headlines,projects,tactics,mandates,objectives,profiles]=bytes.map(b=>JSON.parse(b));
  const sha=b=>createHash('sha256').update(b).digest('hex');
  const studyFiles=['2026-10-09-spatial-counterplay-preregistration.md','2026-10-09-spatial-counterplay-policy.mjs','2026-10-09-spatial-counterplay.mjs'];
  const hashes=Object.fromEntries(await Promise.all(studyFiles.map(async f=>[f,sha(await readFile(`evidence/studies/${f}`))])));
  const identity=await loadGameIdentity({rulesVariant:canonicalRulesVariant(config),profiles:profiles.profiles,backends:['weighted','greedy'],experimentKind:'spatial-counterplay',experimentConfiguration:{smoke,plans}});
  if(identity.provenance.sourceDirty!==false)throw new Error('Identity is dirty');
  const raw={evidenceType:'simulation',generatedAt:new Date().toISOString(),identity,hashes,inputs:Object.fromEntries(files.map((f,i)=>[f,sha(bytes[i])])),smoke,search:{},confirmation:[],sensitivity:[]};
  const rows=[];let games=0;const started=Date.now();
  async function play(block, focalPlan='authored', counterPlan='authored', forcePoint=null) {
    const roster=Array.from({length:block.count},(_,seat)=>factions.factions[(block.faction+seat-block.seat+6)%6]);
    const personas=Array.from({length:block.count},(_,seat)=>profiles.profiles[(block.faction+seat+block.repeat)%profiles.profiles.length]);
    const trace=[];let branchPoint=null;let forced=0;let offers=0;let rejections=0;
    const policies=personas.map((profile,seat)=>new SpatialStudyPolicy(profile,block.backend,{
      scaffold:block.scaffold,plan:seat===block.seat?focalPlan:seat===block.counterSeat?counterPlan:'authored',targetSeat:seat===block.counterSeat?block.seat:null,
      rosterProfileIds:personas.map(p=>p.id),
      force:(packet,chosen,candidates)=>{
        if(packet.requestId!==forcePoint?.requestId)return null;
        if(chosen.decisionId!==forcePoint.originalId)throw new Error('Branch prefix did not reproduce');
        const alternative=candidates.find(d=>d.decisionId===forcePoint.alternativeId);
        if(!alternative)throw new Error('Branch alternative no longer legal');forced++;return alternative;
      },
      observe:({packet,chosen,candidates,ranked})=>{
        const stage=packet.requestId.split(':').at(-2);
        if(packet.observation.publicTable.pendingJointVenture){offers++;rejections+=Number(chosen.decisionId==='agreement_reject');}
        if(chosen.parameters?.destinationId)trace.push({seat,round:packet.round,cycle:packet.cycle,stage,requestId:packet.requestId,
          decisionId:chosen.decisionId,actionId:chosen.actionId,parameters:chosen.parameters,
          alternatives:new Set(candidates.map(d=>d.parameters.destinationId)).size,
          features:ranked.find(r=>r.decision.decisionId===chosen.decisionId)?.features??null});
        if(!branchPoint&&seat!==block.seat&&chosen.actionId==='build'&&chosen.parameters?.facility&&!chosen.parameters.project) {
          const alternatives=candidates.filter(d=>d.parameters.destinationCategory===chosen.parameters.destinationCategory&&
            d.parameters.pieceId===chosen.parameters.pieceId&&d.parameters.actualRunwayCost===chosen.parameters.actualRunwayCost&&
            d.parameters.destinationId!==chosen.parameters.destinationId);
          const board=packet.observation.board;const tile=id=>board.find(t=>t.tileId===id);
          alternatives.sort((a,b)=>distance(tile(chosen.parameters.destinationId),tile(b.parameters.destinationId))-distance(tile(chosen.parameters.destinationId),tile(a.parameters.destinationId))||a.decisionId.localeCompare(b.decisionId));
          if(alternatives.length)branchPoint={requestId:packet.requestId,seat,round:packet.round,cycle:packet.cycle,
            originalId:chosen.decisionId,alternativeId:alternatives[0].decisionId,
            original:chosen.parameters,alternative:alternatives[0].parameters};
        }
      }
    }));
    const m=new SelectedRulesMatch({config,factions:roster,profiles:personas,backends:Array(block.count).fill(block.backend),
      headlines,projects,tactics,mandates,objectives,seed:block.seed,playerCount:block.count,simulateNegotiation:true,recordReplay:false});
    const result=await m.play(policies);
    if(forcePoint&&forced!==1)throw new Error('Branch intervention was not executed exactly once');
    if(!m.complete||result.standings.length!==block.count||m.players.some(p=>['runway','compute','capability','trust','customers','scrutiny','mandate'].some(k=>!Number.isFinite(p[k])||p[k]<0)))throw new Error('Integrity failure');
    const players=m.players.map(p=>({seat:p.seat,factionId:p.factionId,profileId:p.profileId,score:result.standings.find(s=>s.seat===p.seat).score,
      winCredit:result.winnerSeats.includes(p.seat)?1/result.winnerSeats.length:0,
      resources:Object.fromEntries(['runway','compute','capability','trust','customers','scrutiny'].map(k=>[k,p[k]])),
      facilities:p.facilities,connectedFacilities:m.infrastructureState(p).locallyEligible.size,
      activeVentures:m.contracts.filter(c=>(c.left.seat===p.seat||c.right.seat===p.seat)&&activeJointVenture(m,c)).length,
      actions:p.metrics.actions,forcedNoOps:p.metrics.forcedNoOps,policyFallbacks:p.metrics.policyFallbacks,
      locationDecisions:policies[p.seat].locationDecisions,changedDecisions:policies[p.seat].changed}));
    games++;if(games%48===0)process.stderr.write(`${block.stage}: ${games} games complete (${((Date.now()-started)/1000).toFixed(1)}s elapsed)\n`);
    return {focalPlan,counterPlan,winnerSeats:result.winnerSeats,players,trace,branchPoint,forced,offers,rejections};
  }
  const population=Object.keys(plans);
  const subset=(stage,counts,reps)=>smoke?blocks(`smoke-${stage}`,counts,1).slice(0,2):blocks(stage,counts,reps);
  async function search(stage,focal,counter,role) {
    const stageRows=[];
    for(const block of subset(stage,[4],1))for(const plan of population) {
      const outcome=await play(block,role==='counter'?focal:plan,role==='counter'?plan:counter);
      stageRows.push({block,plan,outcome});rows.push({stage,block,plan,outcome});
    }
    const summary=population.map(plan=>{
      const cases=stageRows.filter(r=>r.plan===plan);const players=cases.map(r=>r.outcome.players[role==='counter'?r.block.counterSeat:r.block.seat]);
      return {plan,games:cases.length,winCredit:mean(players.map(p=>p.winCredit)),score:mean(players.map(p=>p.score))};
    }).sort((a,b)=>b.winCredit-a.winCredit||b.score-a.score||a.plan.localeCompare(b.plan));
    raw.search[stage]={winner:summary[0].plan,summary};return summary[0].plan;
  }
  const champion=await search('placement','authored','authored','focal');
  const alternative=raw.search.placement.summary.find(r=>r.plan!==champion&&!['authored','refusal'].includes(r.plan)).plan;
  const counter=await search('counter',champion,'authored','counter');
  const adapted=await search('adaptation',champion,counter,'focal');
  raw.selection={champion,counter,adapted,alternative};raw.training=rows;
  process.stderr.write(`Selection frozen before confirmation: ${JSON.stringify(raw.selection)}\n`);
  for(const block of subset('confirmation',[3,4,5],4)) {
    const arms={};
    for(const [arm,focal,response]of [['authored','authored','authored'],['champion',champion,'authored'],['counter',champion,counter],['adapted',adapted,counter],['immediate','immediate','authored'],['alternative',alternative,'authored']])arms[arm]=await play(block,focal,response);
    raw.confirmation.push({block,arms});
  }
  const confirmationCount=games;
  for(const row of raw.confirmation.filter(r=>r.block.count===4).slice(0,smoke?1:48)) {
    const point=row.arms.champion.branchPoint;
    if(!point){raw.sensitivity.push({block:row.block,opportunity:false});continue;}
    const branch=await play({...row.block,stage:'sensitivity'},champion,'authored',point);
    const choices=outcome=>outcome.trace.filter(t=>t.seat===row.block.seat&&
      (t.round>point.round||t.round===point.round&&t.cycle>=point.cycle));
    const before=choices(row.arms.champion), after=choices(branch);
    const changes=before.flatMap(a=>{
      const b=after.find(b=>b.round===a.round&&b.cycle===a.cycle&&b.stage===a.stage);
      return b&&a.parameters.destinationId!==b.parameters.destinationId?[{round:a.round,cycle:a.cycle,stage:a.stage,
        before:a.parameters.destinationId,after:b.parameters.destinationId,actionChanged:a.actionId!==b.actionId}]:[];
    });
    raw.sensitivity.push({block:row.block,opportunity:true,point,changes,baseline:row.arms.champion.players,branch});
  }
  const effects={championGain:['champion','authored','focal'],geometryGain:['champion','immediate','focal'],
    counterOwnGain:['counter','champion','counter'],championSuppression:['champion','counter','focal'],
    adaptiveRecovery:['adapted','counter','focal'],adaptedGain:['adapted','authored','focal'],adaptedGeometryGain:['adapted','immediate','focal'],alternativeCompetitiveness:['alternative','champion','focal']};
  const summary={};
  for(const count of [3,4,5]) {
    const cases=raw.confirmation.filter(r=>r.block.count===count);if(!cases.length)continue;
    const groups={all:cases,ordinary:cases.filter(r=>!r.block.scaffold),constructionScaffold:cases.filter(r=>r.block.scaffold),weighted:cases.filter(r=>r.block.backend==='weighted'),greedy:cases.filter(r=>r.block.backend==='greedy')};
    summary[count]={};
    for(const [group,cells]of Object.entries(groups)) {
      const stats={blocks:cells.length,arms:{},effects:{}};
      for(const arm of ['authored','champion','counter','adapted','immediate','alternative']) {
        const focal=cells.map(r=>r.arms[arm].players[r.block.seat]);const responders=cells.map(r=>r.arms[arm].players[r.block.counterSeat]);
        stats.arms[arm]={focalWinCredit:mean(focal.map(p=>p.winCredit)),focalScore:mean(focal.map(p=>p.score)),
          counterWinCredit:mean(responders.map(p=>p.winCredit)),counterScore:mean(responders.map(p=>p.score)),
          focalConnectedFacilities:mean(focal.map(p=>p.connectedFacilities)),focalActiveVentures:mean(focal.map(p=>p.activeVentures)),
          offers:cells.reduce((s,r)=>s+r.arms[arm].offers,0),rejections:cells.reduce((s,r)=>s+r.arms[arm].rejections,0)};
      }
      for(const [name,[left,right,role]]of Object.entries(effects)) {
        const differences=cells.map(r=>{const seat=role==='focal'?r.block.seat:r.block.counterSeat;return r.arms[left].players[seat].winCredit-r.arms[right].players[seat].winCredit;});
        stats.effects[name]=pairedInterval(differences);
        const scoreDeltas=cells.map(r=>{const seat=role==='focal'?r.block.seat:r.block.counterSeat;return r.arms[left].players[seat].score-r.arms[right].players[seat].score;});
        stats.effects[name].meanScoreDelta=mean(scoreDeltas);stats.effects[name].scoreInterval=scoreInterval(scoreDeltas);
      }
      summary[count][group]=stats;
    }
  }
  const sensitivity={blocks:raw.sensitivity.length,opportunities:raw.sensitivity.filter(r=>r.opportunity).length,
    changedFocalLocations:raw.sensitivity.filter(r=>r.changes?.length).length,
    changedFocalScores:raw.sensitivity.filter(r=>r.opportunity&&r.baseline[r.block.seat].score!==r.branch.players[r.block.seat].score).length,
    changedFocalWinCredit:raw.sensitivity.filter(r=>r.opportunity&&r.baseline[r.block.seat].winCredit!==r.branch.players[r.block.seat].winCredit).length};
  const primary=summary[4]?.all.effects;
  const gates=primary?{
    consequentialOpponentPlacement:sensitivity.changedFocalScores>0&&sensitivity.changedFocalLocations>0,
    geographyImprovesOverImmediateOnly:primary.geometryGain.lower>0,
    individuallyUsefulCounter:primary.counterOwnGain.lower>0&&primary.championSuppression.lower>0,
    adaptiveRecovery:primary.adaptiveRecovery.lower>=.04,
    competitiveAlternative:primary.alternativeCompetitiveness.lower>=-.18,
    boundedChampionGain:primary.championGain.upper<=.18
  }:{};
  const suffix=smoke?'-smoke':'';const archive=`evidence/studies/simulation/2026-10-09-spatial-counterplay${suffix}-raw.json`;
  await mkdir('evidence/studies/simulation',{recursive:true});const output=JSON.stringify(raw)+'\n';await writeFile(archive,output,{flag:'wx'});
  const receipt={date:'2026-10-09',evidenceType:'simulation',preregistration:studyFiles[0],sourceCommit:identity.provenance.sourceCommit,
    identity,studyHashes:hashes,inputHashes:raw.inputs,smoke,runCount:games,searchAndConfirmationGames:confirmationCount,selection:raw.selection,
    archive,archiveSha256:sha(output),summary,sensitivity,
    gates,verdict:smoke?'smoke_only':Object.values(gates).every(Boolean)?'conditional_counterplay_evidence':'not_established',
    limits:['Bounded public-information placement heuristics; no universal unsolvability claim.',
      'Action bundles follow ordinary policies; half the blocks deliberately scaffold infrastructure.',
      'Venture refusal is a score-leader heuristic, not an optimized negotiation agent.',
      'No experienced human play or independently controlled LLM decisions.',
      'Eight primary paired effects use family-adjusted bounded intervals; thin subgroups are descriptive.',
      'Do not infer overall balance or select rule changes from this spatial study alone.'],
    auditedSurfaces:{engine:'public Venture terms corrected',browser:'same public offer context displayed',
      rules:'no mechanical change',components:'no change',physicalKit:'no mechanical change',referencePlayerAids:'no change',
      tests:'actual legal denial, power prediction, public terms and cleanup',defaultPolicies:'no change',playtestDocumentation:'pending human observations retained'}};
  const receiptPath=`evidence/studies/${smoke?'simulation/':''}2026-10-09-spatial-counterplay${suffix}-receipt.json`;
  await writeFile(receiptPath,JSON.stringify(receipt,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({games,selection:raw.selection,summary:summary[4]?.all,sensitivity,archive,receiptPath}));
  return receipt;
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)await runStudy({smoke:process.argv.includes('--smoke')});
