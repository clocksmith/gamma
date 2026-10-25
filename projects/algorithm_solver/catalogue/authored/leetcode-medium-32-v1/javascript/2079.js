'use strict';

// 2079. Watering Plants: charge each refill its extra round trip.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(plants, capacity) {
  let remaining = capacity;
  let steps = 0;
  for (let index = 0; index < plants.length; index += 1) {
    if (remaining < plants[index]) {
      steps += 2 * index;
      remaining = capacity;
    }
    remaining -= plants[index];
    steps += 1;
  }
  return steps;
}

const wateringPlants = solve;
class Solution {
  wateringPlants(plants, capacity) { return solve(plants, capacity); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, wateringPlants };
