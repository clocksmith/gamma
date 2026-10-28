'use strict';

// 165. Compare Version Numbers (Medium).
// Specification: https://leetcode.com/problems/compare-version-numbers/description/
function solve(version1, version2) {
  const parts1 = version1.split('.').map(Number);
  const parts2 = version2.split('.').map(Number);
  const length = Math.max(parts1.length, parts2.length);
  for (let i = 0; i < length; i++) {
    const a = parts1[i] || 0; const b = parts2[i] || 0;
    if (a < b) return -1; if (a > b) return 1;
  }
  return 0;
}
const compareVersion = solve;
class Solution { compareVersion(version1, version2) { return solve(version1, version2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, compareVersion };
