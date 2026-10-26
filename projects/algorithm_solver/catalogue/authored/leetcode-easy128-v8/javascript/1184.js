'use strict';

// 1184. Distance Between Bus Stops (Easy).
// Specification: https://leetcode.com/problems/distance-between-bus-stops/description/
// O(n) time, O(1) space; compare the two complementary arcs of the circular route.
function solve(distance, start, destination) {
  const first = Math.min(start, destination);
  const last = Math.max(start, destination);
  let total = 0;
  let direct = 0;
  for (let index = 0; index < distance.length; index++) {
    total += distance[index];
    if (index >= first && index < last) direct += distance[index];
  }
  return Math.min(direct, total - direct);
}

const distanceBetweenBusStops = solve;
class Solution {
  distanceBetweenBusStops(distance, start, destination) { return solve(distance, start, destination); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distanceBetweenBusStops };
