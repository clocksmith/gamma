'use strict';

// 2592. Maximize Greatness of an Array: greedily match each larger sorted value to the smallest unmatched value.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const ordered = nums.slice().sort((left, right) => left - right);
  let matched = 0;
  for (const value of ordered) {
    if (value > ordered[matched]) matched += 1;
  }
  return matched;
}

const maximizeGreatness = solve;
class Solution {
  maximizeGreatness(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximizeGreatness };
