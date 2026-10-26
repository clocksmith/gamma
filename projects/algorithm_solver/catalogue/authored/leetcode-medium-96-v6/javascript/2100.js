'use strict';

// 2100. Find Good Days to Rob the Bank: combine the nonincreasing prefix run and nondecreasing suffix run at each day.
// O(n) time and O(n) auxiliary and result space; inputs are read-only.
function solve(security, time) {
  const size = security.length;
  const before = new Int32Array(size);
  const after = new Int32Array(size);
  for (let index = 1; index < size; index += 1) {
    if (security[index] <= security[index - 1]) before[index] = before[index - 1] + 1;
  }
  for (let index = size - 2; index >= 0; index -= 1) {
    if (security[index] <= security[index + 1]) after[index] = after[index + 1] + 1;
  }
  const result = [];
  for (let index = 0; index < size; index += 1) {
    if (before[index] >= time && after[index] >= time) result.push(index);
  }
  return result;
}

const goodDaysToRobBank = solve;
class Solution {
  goodDaysToRobBank(security, time) { return solve(security, time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, goodDaysToRobBank };
