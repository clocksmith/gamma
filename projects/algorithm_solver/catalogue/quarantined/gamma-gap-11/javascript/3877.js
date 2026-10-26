'use strict';

// 3877. Minimum Removals to Achieve Target XOR.
// O(n*2^14) time and O(2^14) space; find a minimum-cardinality removed subset with the required XOR.
function solve(nums, target) {
  const limit = 1 << 14;
  const unreachable = nums.length + 1;
  let best = new Int32Array(limit).fill(unreachable);
  best[0] = 0;
  let total = 0;
  for (const value of nums) {
    total ^= value;
    const following = best.slice();
    for (let state = 0; state < limit; state += 1) {
      if (best[state] < unreachable) following[state ^ value] = Math.min(following[state ^ value], best[state] + 1);
    }
    best = following;
  }
  const answer = best[total ^ target];
  return answer <= nums.length ? answer : -1;
}

const minRemovals = solve;
class Solution {
  minRemovals(nums, target) { return solve(nums, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minRemovals };
