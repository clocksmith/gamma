'use strict';

// 3100. Water Bottles II (Easy).
// Specification: https://leetcode.com/problems/water-bottles-ii/description/
function solve(numBottles, numExchange) {
  let answer = numBottles;
  while (numBottles >= numExchange) {
    numBottles = numBottles - numExchange + 1;
    numExchange++;
    answer++;
  }
  return answer;
}
const maxBottlesDrunk = solve;
class Solution { maxBottlesDrunk(numBottles, numExchange) { return solve(numBottles, numExchange); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxBottlesDrunk };
