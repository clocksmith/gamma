// 523 — Continuous Subarray Sum. Original implementation; authored candidate, not independently qualified.
function solve(nums,k) {
  const first=new Map([[0,-1]]);let remainder=0;
  for(let i=0;i<nums.length;i++){remainder=(remainder+nums[i])%k;if(first.has(remainder)){if(i-first.get(remainder)>=2)return true;}else first.set(remainder,i);}
  return false;
}

module.exports = { solve, checkSubarraySum: solve };
