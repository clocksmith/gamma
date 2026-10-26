'use strict';

// 3780. Maximum Sum of Three Numbers Divisible by Three.
// O(n) time and O(1) auxiliary space; descending cardinalities prevent reusing an index.
function solve(nums) {
  const state = Array.from({ length: 4 }, () => Array(3).fill(-Infinity));
  state[0][0] = 0;
  for (const value of nums) {
    for (let count = 3; count >= 1; count -= 1) {
      for (let remainder = 0; remainder < 3; remainder += 1) {
        const total = state[count - 1][remainder] + value;
        const following = (remainder + value) % 3;
        state[count][following] = Math.max(state[count][following], total);
      }
    }
  }
  return Math.max(0, state[3][0]);
}

const maximumSum = solve;
class Solution {
  maximumSum(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSum };
