'use strict';

// 1877. Minimize Maximum Pair Sum in Array: pair opposite ends of a sorted copy.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const values = [...nums].sort((left, right) => left - right);
  let best = 0;
  for (let left = 0; left < values.length / 2; left += 1) {
    const right = values.length - left - 1;
    best = Math.max(best, values[left] + values[right]);
  }
  return best;
}

const minPairSum = solve;
class Solution {
  minPairSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minPairSum };
