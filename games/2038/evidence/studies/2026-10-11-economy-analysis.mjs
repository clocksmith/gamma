import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {sha256} from '../../lab/versioning/game-identity.js';
import {scenarios} from './2026-10-11-economy-field.mjs';
const mean=xs=>xs.reduce((a,b)=>a+b,0)/xs.length;
const ACTIONS=['fund','research','build','organize','deploy','influence'];
function entropy(values){const total=values.reduce((a,b)=>a+b,0); return total ? -values.filter(x=>x>0).reduce((s,x)=>s+x/total*Math.log(x/total),0)/Math.log(6):0;}
function grouped(players,key){
  const groups={}; for(const p of players){const g=groups[p[key]]??={appearances:0,credit:0,score:0};g.appearances++;g.credit+=p.winCredit;g.score+=p.score;}
  return Object.fromEntries(Object.entries(groups).map(([k,g])=>[k,{...g,winShare:g.credit/g.appearances,meanScore:g.score/g.appearances}]));
}
export function interval(xs){
  if(xs.length<2 || xs.some(x=>!Number.isFinite(x)||Math.abs(x)>1)) throw new RangeError('Invalid paired fraction');
  const n=xs.length,estimate=mean(xs),variance=xs.reduce((s,x)=>s+(x-estimate)**2,0)/(n-1),log=Math.log(4*6/.05);
  const radius=Math.sqrt(2*variance*log/n)+14*log/(3*(n-1));
  return {n,mean:estimate,lower:Math.max(-1,estimate-radius),upper:Math.min(1,estimate+radius),
    method:'fixed-look empirical Bernstein; Bonferroni 6 effects; family alpha .05'};
}
const research=out=>out.players.reduce((s,p)=>s+p.winCredit*(p.actions.research||0)/12,0);
export function summarize(rows){
 const arms={};
 for(const arm of ['canonical','candidate']){
  const games=rows.map(r=>r.arms[arm]),players=games.flatMap(g=>g.players);
  const winnerActions=Object.fromEntries(ACTIONS.map(k=>[k,players.reduce((s,p)=>s+p.winCredit*(p.actions[k]||0),0)/(games.length*12)]));
  const paths={}; for(const p of players) paths[p.winningPath]=(paths[p.winningPath]||0)+p.winCredit/games.length;
  const factions=grouped(players,'factionId'),seats=grouped(players,'seat');
  const range=x=>Math.max(...Object.values(x).map(g=>g.winShare))-Math.min(...Object.values(x).map(g=>g.winShare));
  arms[arm]={games:games.length,winnerActions,winnerActionEntropy:entropy(Object.values(winnerActions)),paths,
    factions,seats,profiles:grouped(players,'profileId'),factionRange:range(factions),seatRange:range(seats),
    noOpRate:players.reduce((s,p)=>s+p.forcedNoOps,0)/(players.length*12),fallbacks:players.reduce((s,p)=>s+p.policyFallbacks,0),
    agiRate:mean(players.map(p=>Number(p.agiDeclared))),meanCustomers:mean(players.map(p=>p.holdings.customers)),
    meanOrgs:mean(players.map(p=>p.orgs)),meanEquipped:mean(players.map(p=>p.equipped)),
    trades:games.map(g=>g.trades),meanScore:mean(players.map(p=>p.score))};
 }
 return {arms,researchEffect:interval(rows.map(r=>research(r.arms.candidate)-research(r.arms.canonical)))};
}
export async function analyze(files){
 const reports=await Promise.all(files.map(async path=>{const bytes=await readFile(path);return {path,sha256:sha256(bytes),report:JSON.parse(bytes)};}));
 const groups={};let candidate=null,identity=null,root=null;
 for(const {report:r} of reports){
  if(r.status!=='complete') throw new Error('Incomplete or smoke report');
  const c=r.options.experimentConfiguration;
  root??=c.root;if(root!==c.root) throw new Error('Mixed seed namespaces');
  candidate??=c.candidate;if(candidate!==c.candidate) throw new Error('Mixed candidates');
  const frozen=JSON.stringify({game:r.identity.game,engine:r.identity.engine,files:r.fileHashes,inputs:r.inputHashes});
  identity??=frozen;if(identity!==frozen) throw new Error('Mixed source/input identities');
  const key=`${c.backend}/${c.count}`;(groups[key]??=[]).push(...r.rows);
 }
 const summaries={};
 for(const [key,rows] of Object.entries(groups)){
  const [backend,count]=key.split('/');const expected=scenarios(Number(count),backend,false,root).map(b=>b.seed).sort();
  if(JSON.stringify(rows.map(r=>r.block.seed).sort())!==JSON.stringify(expected)) throw new Error(`Missing/repeated scenarios: ${key}`);
  summaries[key]=summarize(rows);
 }
 if(Object.keys(groups).length!==6) throw new Error('Missing cohort');
 return {candidate,games:Object.values(groups).reduce((s,r)=>s+r.length*2,0),
   sources:reports.map(({path,sha256})=>({path,sha256})),summaries};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 const [output,...files]=process.argv.slice(2);const report=await analyze(files);
 await writeFile(output,JSON.stringify(report,null,2)+'\n');
 console.log(JSON.stringify(Object.fromEntries(Object.entries(report.summaries).map(([k,s])=>[k,{effect:s.researchEffect,
  arms:Object.fromEntries(Object.entries(s.arms).map(([a,x])=>[a,{research:x.winnerActions.research,entropy:x.winnerActionEntropy,factionRange:x.factionRange,seatRange:x.seatRange,noOps:x.noOpRate}]))}]))));
}
