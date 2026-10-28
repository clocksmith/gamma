'use strict';

// 1518. Water Bottles (Easy).
// Specification: https://leetcode.com/problems/water-bottles/description/
function solve(numBottles, numExchange) {
  let total = numBottles; let empty = numBottles;
  while (empty >= numExchange) {
    const exchanged = Math.floor(empty / numExchange);
    total += exchanged;
    empty = empty % numExchange + exchanged;
  }
  return total;
}
const numWaterBottles = solve;
class Solution { numWaterBottles(numBottles, numExchange) { return solve(numBottles, numExchange); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numWaterBottles };
