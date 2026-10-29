// 517 — Super Washing Machines. Original implementation; authored candidate, not independently qualified.
function solve(machines) {
  const total=machines.reduce((a,b)=>a+b,0),n=machines.length;if(total%n)return -1;
  const average=total/n;let carry=0,answer=0;
  for(const load of machines){carry+=load-average;answer=Math.max(answer,Math.abs(carry),load-average);}
  return answer;
}

module.exports = { solve, findMinMoves: solve };
