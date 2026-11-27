import { readFile, writeFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
const roots=[process.argv[2], process.cwd()];
if (!roots[0]) throw new Error('Pass the compiled frozen baseline game directory.');
const json=async(root,name)=>JSON.parse(await readFile(`${root}/dist/runtime/${name}.json`,'utf8'));
const lanes=[];
for (const root of roots) {
 const {SelectedRulesMatch}=await import(pathToFileURL(`${root}/lab/environment/selected-rules-match.js`));
 const {WeightedPlayerPolicy}=await import(pathToFileURL(`${root}/lab/policies/weighted-policy.js`));
 const [config,factions,headlines,projects,tactics,mandates,objectives,profiles]=await Promise.all(['game-config','factions','headlines','projects','tactics','mandates','secret-objectives','player-strategies'].map(name=>json(root,name)));
 lanes.push({SelectedRulesMatch,WeightedPlayerPolicy,config,factions:factions.factions,headlines,projects,tactics,mandates,objectives,profiles:profiles.profiles});
}
function mechanical(value) { if(Array.isArray(value))return value.map(mechanical);if(!value||typeof value!=='object')return value;return Object.fromEntries(Object.entries(value).filter(([key])=>key!=='kitId' && key!=='verdictBoundary').map(([k,v])=>[k,mechanical(v)])); }
const checks=[];
for(const count of [2,3,4,5])for(let i=0;i<6;i++) {
 const results=[];
 for(const [index,lane]of lanes.entries()) {
  const factions=Array.from({length:count},(_,seat)=>lane.factions[(seat+i)%6]);
  const profiles=Array.from({length:count},(_,seat)=>lane.profiles[(seat+i)%lane.profiles.length]);
  const match=new lane.SelectedRulesMatch({...lane, factions,profiles,seed:`equipment-proof-${count}-${i}`,playerCount:count, recordReplay:true, ...(index ? {kitAssignments:lane.config.playerKits.map(k=>k.id).slice(i%5).concat(lane.config.playerKits.map(k=>k.id).slice(0,i%5)).slice(0,count)}:{})});
  const policies=profiles.map(profile=>new lane.WeightedPlayerPolicy(profile));
  results.push(mechanical(await match.play(policies)));
 }
 assert.deepEqual(results[1],results[0],`${count}p / seed ${i}`);
 checks.push({playerCount:count,seed:`equipment-proof-${count}-${i}`,mechanicallyIdentical:true});
}
await writeFile(process.argv[3] || '/tmp/2038-equipment-equivalence.json',JSON.stringify({evidenceType:'simulation',baselineCommit:'c02a208bf',candidate:'0.21.7',policy:'unchanged weighted',comparison:'complete result and replay excluding only kitId and release-description prose',checks,limits:['Deterministic simulation equivalence; no observed physical teachability claim.']},null,2)+'\n');
console.log(`${checks.length} paired complete games matched exactly`);
