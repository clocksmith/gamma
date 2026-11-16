import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {performance} from 'node:perf_hooks';
import assert from 'node:assert/strict';
import {counter,rng,population,mean,utility,update,freeze,restore} from './runtime.mjs';
const protocol=JSON.parse(fs.readFileSync(new URL('protocol.json',import.meta.url)));
const output=process.argv[2];if(!output)throw Error('Provide new local receipt path');
const sourceHashes=Object.fromEntries(['run.mjs','runtime.mjs','observation.mjs'].map(name=>[name,createHash('sha256').update(fs.readFileSync(new URL(name,import.meta.url))).digest('hex')]));
fs.writeFileSync(`${output}.protocol.json`,JSON.stringify({protocol,sourceHashes},null,2),{flag:'wx'});
const start=performance.now(),initializations=[],records=[];
const arms=['current-retain','current-reset','fixed-retain','fixed-reset','adam','bfgs'];
function train(seed,family,dimension){
 const random=rng(seed),budget=counter(),query=population(seed+10,2,family,dimension);let best;
 for(let k=0;k<33;k++){const phi=Array.from({length:16},()=>random()*2-1);const loss=mean(utility(phi,query,4,budget));if(!best||loss<best.loss)best={phi,loss,candidate:k};}
 const support=population(seed+20,2,family,dimension),test=population(seed+30,2,family,dimension),calibrations={};
 for(const method of ['adam','bfgs']){const cost=counter(),candidates=[];
  for(let k=0;k<33;k++){const rate=method==='adam'?10**(-4+4*Math.floor(k/3)/10):10**(-4+4*k/32),beta=method==='adam'?[0,0.5,0.9][k%3]:0;
   let state={theta:[...best.phi],history:null};const losses=[];
   for(let g=0;g<3;g++){state=update({...state,phi:best.phi,method,rate,beta,id:'calibration',seed:60000+g,
    loss:p=>mean(utility(p,support,4,cost))},cost);losses.push(mean(utility(state.theta,test,4,cost)));}
   candidates.push({rate,beta,loss:mean(losses)});}
  calibrations[method]={budget:cost,candidates,selected:candidates.reduce((a,b)=>b.loss<a.loss?b:a)};
 }
 return{...best,budget,calibrations};
}
for(const family of ['quadratic','logistic'])for(const seed of protocol.seeds){
 const dimension=family==='quadratic'?2:8;
 const initial=train(seed,family,dimension);initializations.push({seed,family,...initial});
 const support=population(seed+100,4,family,dimension),id=`meta/${seed}/${family}`;
 const states=Object.fromEntries(arms.map(arm=>[arm,{theta:[...initial.phi],history:null}]));
 for(let generation=0;generation<3;generation++){
  const proposals=[];
  for(const arm of arms){const before=restore(freeze(states[arm])),budget=counter();if(arm.endsWith('reset'))before.history=null;
   const method=arm==='adam'||arm==='bfgs'?arm:'learned',settings=initial.calibrations[method]?.selected??{};
   const arguments_={...before,phi:arm.startsWith('fixed')?initial.phi:before.theta,method,...settings,id,seed:70000+generation,
    loss:p=>mean(utility(p,support,12,budget))};
   const child=update(arguments_,budget),artifact=freeze(child);
   assert.deepEqual(restore(artifact),child);
   // No operator object or history omitted from the reconstructed child state.
   proposals.push({seed,family,dimension,generation,arm,parent:states[arm].theta,child:restore(artifact),artifact,budget});
  }
  const heldout=population(seed+200+generation,64,family,dimension);
  for(const row of proposals){const scoreBudget=counter();const parentLosses=utility(row.parent,heldout,12,scoreBudget),childLosses=utility(row.child.theta,heldout,12,scoreBudget);
   records.push({...row,parentLosses,childLosses,parentMean:mean(parentLosses),childMean:mean(childLosses),scoreBudget});states[row.arm]=row.child;}
 }
}
const receipt={protocol,sourceHashes,initializations,records,elapsedMs:performance.now()-start,node:process.version};
fs.writeFileSync(output,JSON.stringify(receipt,null,2),{flag:'wx'});
console.log(JSON.stringify({elapsedMs:receipt.elapsedMs,results:records.filter(x=>x.generation===2).map(({seed,family,arm,parentMean,childMean})=>({seed,family,arm,parentMean,childMean}))},null,2));
