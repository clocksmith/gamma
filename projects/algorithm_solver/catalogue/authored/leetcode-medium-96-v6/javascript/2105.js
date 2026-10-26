'use strict';

// 2105. Watering Plants II: advance two watering fronts and use the larger remaining supply at the middle.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(plants, capacityA, capacityB) {
  let left = 0;
  let right = plants.length - 1;
  let waterA = capacityA;
  let waterB = capacityB;
  let refills = 0;
  while (left < right) {
    if (waterA < plants[left]) {
      refills += 1;
      waterA = capacityA;
    }
    waterA -= plants[left];
    if (waterB < plants[right]) {
      refills += 1;
      waterB = capacityB;
    }
    waterB -= plants[right];
    left += 1;
    right -= 1;
  }
  if (left === right && Math.max(waterA, waterB) < plants[left]) refills += 1;
  return refills;
}

const minimumRefill = solve;
class Solution {
  minimumRefill(plants, capacityA, capacityB) { return solve(plants, capacityA, capacityB); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumRefill };
