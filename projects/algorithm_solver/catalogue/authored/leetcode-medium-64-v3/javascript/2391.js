'use strict';

// 2391. Minimum Amount of Time to Collect Garbage: add pickup time and each truck last-needed travel distance.
// O(n + S) time and O(1) auxiliary space for S garbage characters; inputs are read-only.
function solve(garbage, travel) {
  const lastDistance = { M: 0, P: 0, G: 0 };
  let elapsed = 0;
  let pickup = 0;
  for (let index = 0; index < garbage.length; index += 1) {
    if (index > 0) elapsed += travel[index - 1];
    pickup += garbage[index].length;
    for (const kind of garbage[index]) lastDistance[kind] = elapsed;
  }
  return pickup + lastDistance.M + lastDistance.P + lastDistance.G;
}

const garbageCollection = solve;
class Solution {
  garbageCollection(garbage, travel) { return solve(garbage, travel); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, garbageCollection };
