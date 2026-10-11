import {readFile,writeFile} from 'node:fs/promises';
import {execFileSync} from 'node:child_process';
import {isDeepStrictEqual} from 'node:util';
import {SelectedRulesMatch} from '../../lab/environment/selected-rules-match.js';
import {createPlayerPolicy} from '../../lab/policies/policy-factory.js';
import {loadGameIdentity,sha256} from '../../lab/versioning/game-identity.js';
import {RecruitmentPlan,scenarios} from './2026-10-11-early-recruitment.mjs';
import {assertOutcome} from './2026-10-11-capacity-counterplay.mjs';
import {summarizeOutcome} from './2026-10-11-plan-traces.mjs';
if(execFileSync('git',['status','--porcelain'],{encoding:'utf8'}).trim())throw new Error('Clean source required');
const fields=JSON.parse(await readFile('evidence/studies/2026-10-11-economy-profiles.json'));
const profiles=fields.greedy.profiles;
const input=Object.fromEntries(await Promise.all(['game-config','factions','headlines','projects','mandates'].map(async n=>[n,JSON.parse(await readFile(`dist/runtime/${n}.json`))])));
const options={profiles,backends:['greedy'],experimentKind:'equipment_recruitment_stress',policyProjection:'batch'};
const identity=await loadGameIdentity(options),rows=[];
// Complete prior design with independent stress seeds; four arms isolate plan payoff within each price.
for(const count of [3,4,5])for(const b of scenarios(count).filter(b=>b.repeat===0)){
 const block={...b,seed:`equipment-recruit-stress-20261011:${b.seed}`},arms={};
 const byId=id=>profiles.find(p=>p.id===id);
 const base=[byId('balanced_operator'),byId('agi_candidate'),byId('market_maximalist'),byId('power_broker'),byId('balanced_operator')].slice(0,count);
 const roster=base.map((_,i)=>base[(i+count-block.seat)%count]);
 for(const cost of [2,3])for(const plan of ['parent','recruit']){
  const match=new SelectedRulesMatch({config:input['game-config'],factions:block.institutions.map(i=>input.factions.factions[i]),profiles:roster,
   backends:roster.map(()=>'greedy'),headlines:input.headlines,projects:input.projects,mandates:input.mandates,
   seed:block.seed,playerCount:count,mandateMode:block.mode,projection:'batch',rulesVariant:{facilityCost:cost}});
  const policies=roster.map(p=>createPlayerPolicy(p,'greedy',{rosterProfileIds:roster.map(p=>p.id)}));
  policies[block.seat]=new RecruitmentPlan(policies[block.seat],id=>match.legalResolutions(block.seat,id),input['game-config'],plan);
  const result=await match.play(policies);assertOutcome(match,result);
  arms[`${cost}/${plan}`]=summarizeOutcome(result,input['game-config']);
 }
 rows.push({block,arms});if(rows.length%100===0)console.error(`${rows.length} stress scenarios`);
}
if(!isDeepStrictEqual(identity,await loadGameIdentity(options)))throw new Error('Identity drift');
const output='evidence/studies/simulation/2026-10-11-equipment-recruitment.json';
await writeFile(output,JSON.stringify({identity,status:'complete',fileHash:sha256(await readFile(import.meta.filename)),rows})+'\n',{flag:'wx'});
console.log(JSON.stringify({output,scenarios:rows.length,games:rows.length*4}));
