/**
 * 3896. Minimum Operations to Transform Array into Alternating Prime
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-operations-to-transform-array-into-alternating-prime/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3896.Minimum%20Operations%20to%20Transform%20Array%20into%20Alternating%20Prime/README_EN.md
 * Complexity: O(M log log M+n) time, O(M) space.
 * Non-prime includes 1. Inputs preserved; M=max(nums)<=1e5.
 */

function solve(nums) {
  let maximum = 1;
  for (const value of nums) maximum = Math.max(maximum, value);
  const limit = Math.max(4, maximum * 2);
  const prime = new Uint8Array(limit + 1).fill(1);
  prime[0] = prime[1] = 0;
  for (let divisor = 2; divisor * divisor <= limit; divisor += 1) {
    if (prime[divisor]) for (let value = divisor * divisor; value <= limit; value += divisor) prime[value] = 0;
  }
  const nextPrime = new Int32Array(limit + 1);
  let nearest = 0;
  for (let value = limit; value > 0; value -= 1) {
    if (prime[value]) nearest = value;
    nextPrime[value] = nearest;
  }
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    if (index % 2 === 0) answer += nextPrime[value] - value;
    else if (prime[value]) answer += value === 2 ? 2 : 1;
  }
  return answer;
}

function minOperations(nums) {
  return solve(nums);
}

class Solution {
  minOperations(nums) {
    return solve(nums);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minOperations, Solution };
}
