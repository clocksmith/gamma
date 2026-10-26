'use strict';

// 1296. Divide Array in Sets of K Consecutive Numbers: consume consecutive runs beginning at the smallest remaining value.
// O(n log(n + 1)) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  if (nums.length % k !== 0) return false;
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  const starts = Array.from(counts.keys()).sort((a, b) => a - b);
  for (const start of starts) {
    const copies = counts.get(start);
    if (copies === 0) continue;
    for (let value = start; value < start + k; value += 1) {
      const available = counts.get(value) || 0;
      if (available < copies) return false;
      counts.set(value, available - copies);
    }
  }
  return true;
}

const isPossibleDivide = solve;
class Solution {
  isPossibleDivide(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isPossibleDivide };
