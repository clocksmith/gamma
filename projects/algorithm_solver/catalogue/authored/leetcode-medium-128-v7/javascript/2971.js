'use strict';

// 2971. Find Polygon With the Largest Perimeter: take the largest sorted prefix whose previous sides outweigh its largest side.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const ordered = nums.slice().sort((left, right) => left - right);
  let prefix = 0;
  let best = -1;
  for (const value of ordered) {
    if (prefix > value) best = prefix + value;
    prefix += value;
  }
  return best;
}

const largestPerimeter = solve;
class Solution {
  largestPerimeter(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestPerimeter };
