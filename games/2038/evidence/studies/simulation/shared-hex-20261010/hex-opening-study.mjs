import {readFile,writeFile} from 'node:fs/promises';
import {SelectedRulesMatch} from '/Users/xyz/deco/gamma/games/2038/lab/environment/selected-rules-match.js';
import {WeightedPlayerPolicy} from '/Users/xyz/deco/gamma/games/2038/lab/policies/weighted-policy.js';
const root='/Users/xyz/deco/gamma/games/2038';
const read=async name=>JSON.parse(await readFile(`${root}/dist/runtime/${name}.json`,'utf8'));
const config=await read('game-config'),factions=await read('factions'),headlines=await read('headlines'),mandates=await read('mandates'),profiles=(await read('player-strategies')).profiles;
const modes=['adaptive','recruit-first','equip-first','research-first','deploy-first','influence-first'];
const distance=(a,b)=>Math.max(Math.abs(a.q-b.q),Math.abs(a.r-b.r),Math.abs(a.q+a.r-b.q-b.r));
function policy(mode){let turns=0;return {async decide(packet){const {self:p,round,cycle,board,trainingRun:run}=packet.observation;const remaining=13-((round-1)*3+cycle);const seasons=5-round;const value=(key,n)=>{
 if(key==='capability')return Math.min(n,12-p.capability)*1.15;
 if(key==='reputation')return Math.min(n,6-p.reputation)*(p.reputation<4&&p.capability>=7?1.5:1);
 if(key==='customers')return Math.min(n,5-p.customers)*2.3;
 if(key==='compute')return n*(p.compute<2?1.5:p.compute<4?.5:.05)*Math.min(1,remaining/3);
 if(key==='runway')return n*(p.runway<2?.65:p.runway<4?.3:.02)*Math.min(1,remaining/3);
 return 0;};
 const tile=id=>board.find(t=>t.instanceId===id);
 const yieldValue=(org,t)=>t?value(t.yield.resource,t.yield.amount*(org.equipped?2:1))*Math.min(2,seasons):0;
 const reachable=t=>p.pieces.some(org=>!org.tileId||distance(tile(org.tileId),t)<=1);
 const actionValue=id=>({research:p.capability<12?value('capability',2)-value('compute',1):-.1,deploy:p.compute&&p.capability>=(p.customers+1)*2?value('customers',1)-value('reputation',1)-value('compute',1)+.3*seasons:-10,influence:value('reputation',2),fund:value('runway',2),build:p.runway>=2&&p.pieces.some(o=>!o.equipped)?.6*seasons:0,organize:p.runway>=2&&p.agentsInSupply?.55*seasons:0})[id]||0;
 function score(d){const a=d.parameters||{},c=d.consequences||{};
 if(d.decisionId==='agi_declare')return 100;
 if(d.decisionId==='agi_pass')return 0;
 if(d.decisionId==='research_bank')return run.provisionalCapability>=2||p.capability+run.provisionalCapability>=12?100:0;
 if(d.decisionId==='research_continue')return 5;
 if(d.decisionId==='research_pay_bank')return 10;
 if(d.decisionId==='trade_none')return 0;
 if(d.decisionId==='trade_accept')return p.compute<2||p.runway<2?1:-1;
 if(d.decisionId==='trade_reject')return 0;
 if(d.actionId==='trade')return value(a.receiveResource,a.receiveAmount)-value(a.giveResource,a.giveAmount)-.05;
 if(c.stage==='action_selection'){
 if(c.resolvableWithoutTrade===false)return -100;
 const preferred={'recruit-first':'organize','equip-first':'build','research-first':'research','deploy-first':'deploy','influence-first':'influence'}[mode];
 const bonus=turns<2&&d.actionId===preferred?20:0;
 const locations=board.filter(t=>t.actionId===d.actionId&&reachable(t));
 const locationGain=Math.max(0,...locations.flatMap(t=>p.pieces.filter(o=>!o.tileId||distance(tile(o.tileId),t)<=1).map(o=>yieldValue(o,t)-yieldValue(o,tile(o.tileId)))));
 return actionValue(d.actionId)+locationGain*.5+bonus;
 }
 let s=Object.entries(c).reduce((sum,[key,n])=>sum+(typeof n==='number'?(n<0?-value(key,-n):value(key,n)):0),0);
 const org=p.pieces.find(o=>o.id===a.pieceId),dest=tile(a.destinationId);
 if(org&&dest){s+=.5*(yieldValue(org,dest)-yieldValue(org,tile(org.tileId)));s+=.25*board.filter(t=>['research','deploy','influence'].includes(t.actionId)&&distance(dest,t)<=1).length;}
 if(a.equipOrgId){const o=p.pieces.find(o=>o.id===a.equipOrgId);s+=yieldValue({...o,equipped:false},o.id===org?.id?dest:tile(o.tileId));}
 if(a.mode==='recruit')s+=.55*seasons+(turns<=2&&mode==='recruit-first'?20:0);
 if(a.mode==='reassign'){const o=p.pieces.find(o=>o.id===a.otherAgentId);s+=yieldValue(o,tile(a.otherAreaId))-yieldValue(o,tile(o.tileId));}
 return s;}
 const ranked=packet.legalDecisions.map(d=>({d,s:score(d)})).sort((a,b)=>b.s-a.s||a.d.decisionId.localeCompare(b.d.decisionId));if(ranked[0].d.consequences?.stage==='action_selection')turns++;
 return {decision:{decisionId:ranked[0].d.decisionId,rationale:mode},receipt:{provider:'opening-study',profileId:mode}};
 }};}
const rows=[];const blocks=Number(process.env.BLOCKS||6);
for(const count of [3,4,5])for(let block=0;block<blocks;block++)for(let shift=0;shift<6;shift++)for(let focal=0;focal<count;focal++){
 const roster=Array.from({length:count},(_,seat)=>factions.factions[(seat+shift)%6]);
 const mode=modes[(block+focal)%modes.length];
 const m=new SelectedRulesMatch({config,factions:roster,profiles,headlines,mandates,playerCount:count,seed:`opening-20261010:${block}:${shift}:${count}`});
 const result=await m.play(Array.from({length:count},(_,seat)=>policy(seat===focal?mode:'adaptive')));
 const p=result.standings.find(p=>p.seat===focal);rows.push({count,block,shift,focal,mode,faction:p.factionId,score:p.score,win:result.winnerSeats.includes(focal)?1/result.winnerSeats.length:0,orgs:p.pieces.length,equipped:p.equippedOrgs,actions:p.metrics.actions});
}
const stats=Object.fromEntries(modes.map(mode=>{const a=rows.filter(r=>r.mode===mode);return[mode,{n:a.length,score:a.reduce((s,r)=>s+r.score,0)/a.length,win:a.reduce((s,r)=>s+r.win,0)/a.length,orgs:a.reduce((s,r)=>s+r.orgs,0)/a.length}]}));
await writeFile('/tmp/hex-opening-results.json',JSON.stringify({stats,rows},null,2));console.log(JSON.stringify(stats,null,2));
