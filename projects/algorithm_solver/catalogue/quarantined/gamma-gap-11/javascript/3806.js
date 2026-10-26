'use strict';

// 3806. Maximum Bitwise AND After Increment Operations.
// O(B n log n) time and O(n) space, B <= 31; exact bounded integers and read-only inputs.
function solve(nums, k, m) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  let answer = 0;
  for (let bit = Math.floor(Math.log2(maximum + k)); bit >= 0; bit -= 1) {
    const candidate = answer | (2 ** bit);
    const costs = [];
    for (const value of nums) {
      const missing = candidate & ~value;
      if (missing === 0) {
        costs.push(0);
      } else {
        const pivot = 2 ** (31 - Math.clz32(missing));
        const raised = value - value % (2 * pivot) + pivot + candidate % pivot;
        costs.push(raised - value);
      }
    }
    costs.sort((left, right) => left - right);
    let spent = 0;
    for (let index = 0; index < m && spent <= k; index += 1) spent += costs[index];
    if (spent <= k) answer = candidate;
  }
  return answer;
}

const maximumAND = solve;
class Solution {
  maximumAND(nums, k, m) { return solve(nums, k, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumAND };
