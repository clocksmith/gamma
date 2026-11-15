import fs from 'node:fs';
import {summarize} from '../self_transform_v7/analyze.mjs';
const receipt=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const results=[];
for(const family of ['quadratic','logistic']){
 const current=receipt.records.filter(x=>x.family===family&&x.generation===2&&x.arm==='current-retain');
 if(current.length!==12)throw Error('Expected12 independent replicates');
 for(const comparator of ['fixed-retain','current-reset','adam','bfgs']){
  const effects=current.map(x=>{
   const y=receipt.records.find(y=>y.family===family&&y.seed===x.seed&&y.generation===2&&y.arm===comparator);
   return{seed:x.seed,relative:(y.childMean-x.childMean)/y.childMean,absolute:y.childMean-x.childMean};
  });
  const summary=summarize(effects.map(x=>x.relative),1e-6);
  results.push({family,comparator,effects,summary,primary:comparator==='fixed-retain',
   passes:comparator==='fixed-retain'?summary.median>=0.01&&summary.oneSidedSignP<0.025:null});
 }
}
console.log(JSON.stringify(results,null,2));
