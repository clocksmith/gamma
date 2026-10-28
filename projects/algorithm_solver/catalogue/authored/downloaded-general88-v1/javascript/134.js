'use strict';

// 134. Gas Station (Medium).
// Specification: https://leetcode.com/problems/gas-station/description/
function solve(gas, cost) {
  let total = 0; let tank = 0; let start = 0;
  for (let i = 0; i < gas.length; i++) {
    total += gas[i] - cost[i];
    tank += gas[i] - cost[i];
    if (tank < 0) { start = i + 1; tank = 0; }
  }
  return total >= 0 ? start : -1;
}
const canCompleteCircuit = solve;
class Solution { canCompleteCircuit(gas, cost) { return solve(gas, cost); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, canCompleteCircuit };
