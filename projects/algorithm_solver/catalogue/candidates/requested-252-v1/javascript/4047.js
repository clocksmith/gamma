/**
 * 4047. Minimum Operations to Make XOR of All Elements Zero
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-make-xor-of-all-elements-zero/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4047.Minimum%20Operations%20to%20Make%20XOR%20of%20All%20Elements%20Zero/README_EN.md
 * Complexity: O(n + 2048U) time, O(2048+U) space, U distinct values.
 * Each elementary XOR row operation is invertible; backwards from the all-ones coefficient vector it changes at most one coefficient. Thus the minimum donor subset whose XOR is the total is a lower bound. A minimum subset is linearly independent. When its complement is nonempty and values are not all identical, choose a complement accumulator and order donors so no prefix cancels it, attaining the bound without XORing equal values. A minimum subset of size n means independence and impossibility. Inputs preserved.
 */

function solve(nums) {
  let target=0;for(const x of nums)target^=x;
  if(target===0)return 0;
  const values=Array.from(new Set(nums));
  if(values.length===1)return -1;
  const distance=new Int16Array(2048);distance.fill(-1);distance[0]=0;
  const queue=[0];
  for(let head=0;head<queue.length;head++) {
    const state=queue[head],next=distance[state]+1;
    for(const value of values) {
      const neighbor=state^value;
      if(distance[neighbor]!==-1)continue;
      if(neighbor===target)return next<nums.length?next:-1;
      distance[neighbor]=next;queue.push(neighbor);
    }
  }
  return -1;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
