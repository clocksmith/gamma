'use strict';

// 3176. Find the Maximum Length of a Good Subsequence I: track best ending values for each permitted count of adjacent changes.
// O(n * (k + 1)) expected time and O(u * (k + 1)) space for u distinct values; inputs are read-only.
function solve(nums, k) {
  const endings = new Map();
  const best = new Array(k + 1).fill(0);
  for (const value of nums) {
    if (!endings.has(value)) endings.set(value, new Array(k + 1).fill(0));
    const same = endings.get(value);
    // Descending budgets prevent a transition from consuming this value twice.
    for (let changes = k; changes >= 0; changes -= 1) {
      let candidate = same[changes] + 1;
      if (changes > 0) candidate = Math.max(candidate, best[changes - 1] + 1);
      same[changes] = candidate;
      best[changes] = Math.max(best[changes], candidate);
    }
  }
  return best[k];
}

const maximumLength = solve;
class Solution {
  maximumLength(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumLength };
