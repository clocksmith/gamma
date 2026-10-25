'use strict';

// 2597. The Number of Beautiful Subsets: combine independent residue groups with skip/take dynamic programming.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  const groups = new Map();
  for (const [value, frequency] of counts) {
    const remainder = value % k;
    if (!groups.has(remainder)) groups.set(remainder, []);
    groups.get(remainder).push([value, frequency]);
  }
  let answer = 1;
  for (const group of groups.values()) {
    group.sort((left, right) => left[0] - right[0]);
    let skipped = 1;
    let taken = 0;
    let previous = null;
    for (const [value, frequency] of group) {
      const choices = 2 ** frequency - 1;
      const total = skipped + taken;
      const available = previous !== null && value - previous === k ? skipped : total;
      const nextTaken = choices * available;
      skipped = total;
      taken = nextTaken;
      previous = value;
    }
    answer *= skipped + taken;
  }
  return answer - 1;
}

const beautifulSubsets = solve;
class Solution {
  beautifulSubsets(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, beautifulSubsets };
