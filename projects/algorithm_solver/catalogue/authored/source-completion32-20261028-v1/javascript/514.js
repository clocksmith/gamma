// 514 — Freedom Trail. Original implementation; authored candidate, not independently qualified.
function solve(ring,key) {
  const positions=new Map();for(let i=0;i<ring.length;i++){if(!positions.has(ring[i]))positions.set(ring[i],[]);positions.get(ring[i]).push(i);}
  let costs=new Map([[0,0]]);
  for(const char of key){const next=new Map();for(const end of positions.get(char)){let best=Infinity;for(const [start,cost] of costs){const distance=Math.abs(start-end);best=Math.min(best,cost+Math.min(distance,ring.length-distance)+1);}next.set(end,best);}costs=next;}
  return Math.min(...costs.values());
}

module.exports = { solve, findRotateSteps: solve };
