'use strict';

// 1710. Maximum Units on a Truck (Easy).
// Specification: https://leetcode.com/problems/maximum-units-on-a-truck/description/
// O(n log n) time, O(n) space; load the highest units per box first using a sorted copy.
function solve(boxTypes, truckSize) {
  const ordered = boxTypes.slice().sort((a, b) => b[1] - a[1]);
  let remaining = truckSize;
  let total = 0;
  for (const [count, units] of ordered) {
    const loaded = Math.min(count, remaining);
    total += loaded * units;
    remaining -= loaded;
    if (remaining === 0) break;
  }
  return total;
}

const maximumUnits = solve;
class Solution {
  maximumUnits(boxTypes, truckSize) { return solve(boxTypes, truckSize); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumUnits };
