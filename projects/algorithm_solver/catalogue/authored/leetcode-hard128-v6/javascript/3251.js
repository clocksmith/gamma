'use strict';

// 3251. Find the Count of Monotonic Pairs II.
// Prefix sums aggregate valid preceding first-array values; O(n*M) time and O(M) space for M=max(nums). Inputs are preserved.

function solve(nums) {
  const modulus = 1000000007;
  let previous = Array(nums[0] + 1).fill(1);
  for (let index = 1; index < nums.length; index += 1) {
    for (let value = 1; value < previous.length; value += 1) previous[value] = (previous[value] + previous[value - 1]) % modulus;
    const current = Array(nums[index] + 1).fill(0), shift = Math.min(0, nums[index - 1] - nums[index]);
    for (let value = 0; value < current.length; value += 1) {
      const limit = Math.min(previous.length - 1, value + shift);
      if (limit >= 0) current[value] = previous[limit];
    }
    previous = current;
  }
  return previous.reduce((sum, value) => (sum + value) % modulus, 0);
}

const countOfPairs = solve;
class Solution {
  countOfPairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countOfPairs };
