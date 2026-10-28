'use strict';

// 1013. Partition Array Into Three Parts With Equal Sum (Easy).
// Specification: https://leetcode.com/problems/partition-array-into-three-parts-with-equal-sum/description/
function solve(arr) {
  const total = arr.reduce((sum, value) => sum + value, 0);
  if (total % 3 !== 0) return false;
  const part = total / 3;
  let current = 0; let found = 0;
  for (let i = 0; i < arr.length - 1; i++) {
    current += arr[i];
    if (current === part) { found++; current = 0; if (found === 2) return true; }
  }
  return false;
}
const canThreePartsEqualSum = solve;
class Solution { canThreePartsEqualSum(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canThreePartsEqualSum };
