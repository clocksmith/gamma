'use strict';

// 2554. Maximum Number of Integers to Choose From a Range I (Easy).
// Specification: https://leetcode.com/problems/maximum-number-of-integers-to-choose-from-a-range-i/description/
function solve(banned, n, maxSum) {
  const bannedSet = new Set(banned);
  let sum = 0; let cnt = 0;
  for (let x = 1; x <= n; x++) {
    if (bannedSet.has(x)) continue;
    if (sum + x > maxSum) break;
    sum += x; cnt++;
  }
  return cnt;
}
const maxCount = solve;
class Solution { maxCount(banned, n, maxSum) { return solve(banned, n, maxSum); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxCount };
