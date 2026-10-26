'use strict';

// 2763. Sum of Imbalance Numbers of All Subarrays: incremental connected components among distinct integers.
// O(n^2) expected time and O(n) auxiliary space. Inputs are preserved.
function solve(nums) {
  let answer = 0;
  for (let left = 0; left < nums.length; left += 1) {
    const seen = new Set();
    let imbalance = -1;
    for (let right = left; right < nums.length; right += 1) {
      const value = nums[right];
      if (!seen.has(value)) {
        imbalance += 1 - Number(seen.has(value - 1)) - Number(seen.has(value + 1));
        seen.add(value);
      }
      answer += imbalance;
    }
  }
  return answer;
}

const sumImbalanceNumbers = solve;
class Solution {
  sumImbalanceNumbers(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumImbalanceNumbers };
