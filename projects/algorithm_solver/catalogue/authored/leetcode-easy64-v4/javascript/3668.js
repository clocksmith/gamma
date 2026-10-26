'use strict';

// 3668. Restore Finishing Order (Easy).
// Specification: https://leetcode.com/problems/restore-finishing-order/description/
// O(n + f) expected time, O(f) space; preserve both input arrays.
function solve(order, friends) {
  const friendIds = new Set(friends);
  const result = [];
  for (const participant of order) {
    if (friendIds.has(participant)) result.push(participant);
  }
  return result;
}

const recoverOrder = solve;
class Solution {
  recoverOrder(order, friends) { return solve(order, friends); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, recoverOrder };
