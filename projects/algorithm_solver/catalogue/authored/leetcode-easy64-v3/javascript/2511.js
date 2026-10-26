'use strict';

// 2511. Maximum Enemy Forts That Can Be Captured (Easy).
// Specification: https://leetcode.com/problems/maximum-enemy-forts-that-can-be-captured/description/
// O(n) time, O(1) space; inspect gaps between opposite nonzero endpoints.
function solve(forts) {
  let previous = -1;
  let largest = 0;
  for (let index = 0; index < forts.length; index++) {
    if (forts[index] === 0) continue;
    if (previous !== -1 && forts[index] !== forts[previous]) {
      largest = Math.max(largest, index - previous - 1);
    }
    previous = index;
  }
  return largest;
}

const captureForts = solve;
class Solution {
  captureForts(forts) { return solve(forts); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, captureForts };
