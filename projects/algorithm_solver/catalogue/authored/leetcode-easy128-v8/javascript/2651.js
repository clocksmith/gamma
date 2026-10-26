'use strict';

// 2651. Calculate Delayed Arrival Time (Easy).
// Specification: https://leetcode.com/problems/calculate-delayed-arrival-time/description/
// O(1) time and space; wrap the delayed hour into the 24-hour clock.
function solve(arrivalTime, delayedTime) {
  return (arrivalTime + delayedTime) % 24;
}

const findDelayedArrivalTime = solve;
class Solution {
  findDelayedArrivalTime(arrivalTime, delayedTime) { return solve(arrivalTime, delayedTime); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDelayedArrivalTime };
