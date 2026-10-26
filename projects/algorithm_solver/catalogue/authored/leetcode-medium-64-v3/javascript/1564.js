'use strict';

// 1564. Put Boxes Into the Warehouse I: fill deepest usable rooms with the smallest remaining boxes.
// O(b log b + w) time and O(b + w) space for b boxes and w rooms; inputs are read-only.
function solve(boxes, warehouse) {
  const ordered = [...boxes].sort((left, right) => left - right);
  const capacities = [];
  let bottleneck = Infinity;
  for (const height of warehouse) {
    bottleneck = Math.min(bottleneck, height);
    capacities.push(bottleneck);
  }
  let placed = 0;
  for (let index = capacities.length - 1; index >= 0; index -= 1) {
    if (placed < ordered.length && ordered[placed] <= capacities[index]) placed += 1;
  }
  return placed;
}

const maxBoxesInWarehouse = solve;
class Solution {
  maxBoxesInWarehouse(boxes, warehouse) { return solve(boxes, warehouse); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxBoxesInWarehouse };
