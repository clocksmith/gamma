'use strict';

// 1701. Average Waiting Time: advance the single chef clock and sum each customer completion delay.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(customers) {
  let finished = 0;
  let totalWait = 0;
  for (const [arrival, preparation] of customers) {
    finished = Math.max(finished, arrival) + preparation;
    totalWait += finished - arrival;
  }
  return totalWait / customers.length;
}

const averageWaitingTime = solve;
class Solution {
  averageWaitingTime(customers) { return solve(customers); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, averageWaitingTime };
