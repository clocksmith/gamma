// 525 — Contiguous Array. Original implementation; authored candidate, not independently qualified.
function solve(nums) {
  const first=new Map([[0,-1]]);let balance=0,answer=0;
  for(let i=0;i<nums.length;i++){balance+=nums[i]===1?1:-1;if(first.has(balance))answer=Math.max(answer,i-first.get(balance));else first.set(balance,i);}return answer;
}

module.exports = { solve, findMaxLength: solve };
