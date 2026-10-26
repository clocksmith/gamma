'use strict';

// 2501. Longest Square Streak in an Array: process distinct values in increasing order and extend exact square chains.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const lengths = new Map();
  const ordered = Array.from(new Set(nums)).sort((left, right) => left - right);
  let best = 0;
  for (const value of ordered) {
    const root = Math.floor(Math.sqrt(value));
    const length = root * root === value ? (lengths.get(root) || 0) + 1 : 1;
    lengths.set(value, length);
    best = Math.max(best, length);
  }
  return best >= 2 ? best : -1;
}

const longestSquareStreak = solve;
class Solution {
  longestSquareStreak(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestSquareStreak };
