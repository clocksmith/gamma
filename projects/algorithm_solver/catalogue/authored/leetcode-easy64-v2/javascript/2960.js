'use strict';

// 2960. Count Tested Devices After Test Operations (Easy).
// Specification: https://leetcode.com/problems/count-tested-devices-after-test-operations/description/
// O(n) time, O(1) space; prior successful tests account for all decrements.
function solve(batteryPercentages) {
  let tested = 0;
  for (const percentage of batteryPercentages) {
    if (percentage > tested) tested++;
  }
  return tested;
}

const countTestedDevices = solve;
class Solution {
  countTestedDevices(batteryPercentages) { return solve(batteryPercentages); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countTestedDevices };
