'use strict';

// 3678. Smallest Absent Positive Greater Than Average (Easy).
// Specification: https://leetcode.com/problems/smallest-absent-positive-greater-than-average/description/
// O(n) expected time and space; use floor division, including negative sums.
function solve(nums) {
  const present = new Set(nums);
  let total = 0;
  for (const value of nums) total += value;
  let candidate = Math.max(1, Math.floor(total / nums.length) + 1);
  while (present.has(candidate)) candidate++;
  return candidate;
}

const smallestAbsent = solve;
class Solution {
  smallestAbsent(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestAbsent };
