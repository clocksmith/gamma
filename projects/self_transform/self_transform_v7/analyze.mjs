import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
export function signProbability(wins, losses) {
  const n = wins + losses;
  if (!n) return 1;
  let sum = 0, coefficient = 1;
  for (let k = 0; k <= n; k += 1) {
    if (k >= wins) sum += coefficient;
    coefficient = coefficient * (n - k) / (k + 1);
  }
  return sum / 2 ** n;
}
export function summarize(effects, tolerance) {
  const sorted = [...effects].sort((a,b)=>a-b), n = sorted.length;
  if (!n || !sorted.every(Number.isFinite)) throw new Error('Invalid effects');
  const wins = effects.filter(x=>x>tolerance).length;
  const losses = effects.filter(x=>x < -tolerance).length;
  return { n, wins, losses, ties:n-wins-losses,
    median: (sorted[Math.floor((n-1)/2)] + sorted[Math.floor(n/2)]) / 2,
    mean: effects.reduce((a,b)=>a+b,0)/n,
    min: sorted[0], max: sorted[n-1], oneSidedSignP: signProbability(wins,losses),
    medianOrderStatisticInterval: n===12 ? {low:sorted[2],high:sorted[9],
      coverage:1-2*(1+12+66)/4096,
      assumption:'Independent exchangeable replicate effects; descriptive interval, not an extra decision rule'} : null };
}
export function analyze(receipt) {
  const p=receipt.protocol.primaryEndpoint;
  const rows=receipt.records.filter(x=>x.initializer===p.initializer
    &&x.generation===p.generation&&x.arm==='hereditary');
  const effects=rows.map(x=>{
    const fixed=receipt.records.find(y=>y.seed===x.seed&&y.initializer===p.initializer
      &&y.generation===p.generation&&y.arm==='fixed_proposer');
    if(!fixed || fixed.childMean<=0) throw new Error('Missing or invalid comparator');
    return {seed:x.seed,absolute:fixed.childMean-x.childMean,
      relative:(fixed.childMean-x.childMean)/fixed.childMean};
  });
  if(effects.length!==receipt.protocol.replicateSeeds.length) throw new Error('Missing replicates');
  const summary=summarize(effects.map(x=>x.relative),p.relativeTieTolerance);
  return {effects,summary,passes:summary.median>=p.minimumMedianRelativeImprovement
    &&summary.oneSidedSignP<p.oneSidedSignTestAlpha};
}
if(process.argv[1] && import.meta.url===pathToFileURL(process.argv[1]).href) {
  console.log(JSON.stringify(analyze(JSON.parse(fs.readFileSync(process.argv[2],'utf8'))),null,2));
}
