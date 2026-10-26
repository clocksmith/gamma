'use strict';

// 1819. Number of Different Subsequences GCDs. Sieve of present multiples; O(n + M log(M)^2) time and O(M) space, M=max(nums). Inputs are preserved.

function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const present = new Uint8Array(maximum + 1);
  for (const value of nums) present[value] = 1;
  function gcd(first, second) {
    while (second !== 0) [first, second] = [second, first % second];
    return first;
  }
  let answer = 0;
  for (let candidate = 1; candidate <= maximum; candidate += 1) {
    let common = 0;
    for (let multiple = candidate; multiple <= maximum; multiple += candidate) {
      if (present[multiple]) {
        common = gcd(common, multiple);
        if (common === candidate) {
          answer += 1;
          break;
        }
      }
    }
  }
  return answer;
}

const countDifferentSubsequenceGCDs = solve;
class Solution {
  countDifferentSubsequenceGCDs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countDifferentSubsequenceGCDs };
