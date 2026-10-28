'use strict';

// 1773. Count Items Matching a Rule (Easy).
// Specification: https://leetcode.com/problems/count-items-matching-a-rule/description/
const INDEX = { type: 0, color: 1, name: 2 };
function solve(items, ruleKey, ruleValue) {
  const index = INDEX[ruleKey];
  let count = 0;
  for (const item of items) { if (item[index] === ruleValue) count++; }
  return count;
}
const countMatches = solve;
class Solution { countMatches(items, ruleKey, ruleValue) { return solve(items, ruleKey, ruleValue); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, countMatches };
