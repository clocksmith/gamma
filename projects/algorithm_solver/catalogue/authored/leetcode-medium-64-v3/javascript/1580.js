'use strict';

// 1580. Put Boxes Into the Warehouse II: match boxes to capacities reachable from either entrance.
// O(b log b + w log w) time and O(b + w) auxiliary space; inputs are read-only.
function solve(boxes, warehouse) {
  const ordered = [...boxes].sort((left, right) => left - right);
  const capacities = [];
  let bottleneck = Infinity;
  for (const height of warehouse) {
    bottleneck = Math.min(bottleneck, height);
    capacities.push(bottleneck);
  }
  bottleneck = Infinity;
  for (let index = warehouse.length - 1; index >= 0; index -= 1) {
    bottleneck = Math.min(bottleneck, warehouse[index]);
    capacities[index] = Math.max(capacities[index], bottleneck);
  }
  capacities.sort((left, right) => left - right);
  let placed = 0;
  for (const capacity of capacities) {
    if (placed < ordered.length && ordered[placed] <= capacity) placed += 1;
  }
  return placed;
}

const maxBoxesInWarehouse = solve;
class Solution {
  maxBoxesInWarehouse(boxes, warehouse) { return solve(boxes, warehouse); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxBoxesInWarehouse };
