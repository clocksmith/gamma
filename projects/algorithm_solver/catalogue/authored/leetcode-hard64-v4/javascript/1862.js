'use strict';

// 1862. Sum of Floored Pairs. Frequency prefix sums over quotient ranges; O(n+M log M) time and O(M) space. Inputs are preserved.

function solve(nums) {
  const modulus = 1000000007;
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const frequency = new Int32Array(maximum + 1);
  for (const value of nums) frequency[value] += 1;
  const prefix = new Int32Array(maximum + 1);
  for (let value = 1; value <= maximum; value += 1) prefix[value] = prefix[value - 1] + frequency[value];
  let answer = 0;
  for (let denominator = 1; denominator <= maximum; denominator += 1) {
    if (frequency[denominator] === 0) continue;
    for (let left = denominator; left <= maximum; left += denominator) {
      const right = Math.min(maximum, left + denominator - 1);
      const amount = prefix[right] - prefix[left - 1];
      // The problem's n,M <= 100000 bounds keep this integer product below 2^53.
      answer = (answer + frequency[denominator] * amount * (left / denominator)) % modulus;
    }
  }
  return answer;
}

const sumOfFlooredPairs = solve;
class Solution {
  sumOfFlooredPairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfFlooredPairs };
