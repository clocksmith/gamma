'use strict';

// 3177. Find the Maximum Length of a Good Subsequence II.
// DP by final value and allowed changes, updated in descending budget order; O(n*k) expected time, O(U*k) space. Inputs are preserved.

function solve(nums, k) {
  const endings = new Map(), best = Array(k + 1).fill(0);
  for (const value of nums) {
    if (!endings.has(value)) endings.set(value, Array(k + 1).fill(0));
    const row = endings.get(value);
    for (let changes = k; changes >= 0; changes -= 1) {
      row[changes] = Math.max(row[changes] + 1, changes > 0 ? best[changes - 1] + 1 : 1);
      best[changes] = Math.max(best[changes], row[changes]);
    }
  }
  return best[k];
}

const maximumLength = solve;
class Solution {
  maximumLength(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumLength };
