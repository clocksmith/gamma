// 399 — Evaluate Division. Original implementation; authored candidate, not independently qualified.
function solve(equations, values, queries) {
  const graph=new Map();
  equations.forEach(([a,b],i)=>{if(!graph.has(a))graph.set(a,[]);if(!graph.has(b))graph.set(b,[]);graph.get(a).push([b,values[i]]);graph.get(b).push([a,1/values[i]]);});
  return queries.map(([start,target])=>{if(!graph.has(start)||!graph.has(target))return -1;const stack=[[start,1]],seen=new Set([start]);while(stack.length){const [v,ratio]=stack.pop();if(v===target)return ratio;for(const [next,weight] of graph.get(v))if(!seen.has(next)){seen.add(next);stack.push([next,ratio*weight]);}}return -1;});
}

module.exports = { solve, calcEquation: solve };
