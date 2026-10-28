'use strict';

// 1094. Car Pooling (Medium).
// Specification: https://leetcode.com/problems/car-pooling/description/
function solve(trips, capacity) {
  const changes = new Array(1001).fill(0);
  for (const [passengers, from, to] of trips) { changes[from] += passengers; changes[to] -= passengers; }
  let current = 0;
  for (const change of changes) { current += change; if (current > capacity) return false; }
  return true;
}
const carPooling = solve;
class Solution { carPooling(trips, capacity) { return solve(trips, capacity); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, carPooling };
