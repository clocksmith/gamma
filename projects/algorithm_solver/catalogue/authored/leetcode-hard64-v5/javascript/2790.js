'use strict';

// 2790. Maximum Number of Groups With Increasing Length. Process increasing capacities and add at most one distinct-element group per value; O(n log n) time and O(n) space. Inputs are preserved.

function solve(usageLimits) {
  let available = 0;
  let groups = 0;
  for (const limit of usageLimits.slice().sort((a, b) => a - b)) {
    available += limit;
    if (available >= (groups + 1) * (groups + 2) / 2) groups += 1;
  }
  return groups;
}

const maxIncreasingGroups = solve;
class Solution {
  maxIncreasingGroups(usageLimits) { return solve(usageLimits); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxIncreasingGroups };
