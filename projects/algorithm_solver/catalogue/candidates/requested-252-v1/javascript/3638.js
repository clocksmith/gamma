'use strict';

// 3638. Maximum Balanced Shipments.
// Specification: https://leetcode.com/problems/maximum-balanced-shipments/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n) time, O(1) space; greedily end each shipment at its first strict drop below its maximum.
// Inputs are not modified.

function solve(weight) {
  let maximum = -Infinity, answer = 0;
  for (const value of weight) {
    if (value < maximum) { answer++; maximum = -Infinity; }
    else maximum = value;
  }
  return answer;
}

const maxBalancedShipments = solve;
class Solution {
  maxBalancedShipments(weight) { return solve(weight); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxBalancedShipments };
