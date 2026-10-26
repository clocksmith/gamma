'use strict';

// 1584. Min Cost to Connect All Points: run dense Prim without materializing the complete Manhattan graph.
// O(n^2) time and O(n) auxiliary space; inputs are read-only.
function solve(points) {
  const size = points.length;
  const distance = new Array(size).fill(Infinity);
  distance[0] = 0;
  const used = new Uint8Array(size);
  let total = 0;
  for (let step = 0; step < size; step += 1) {
    let chosen = -1;
    for (let node = 0; node < size; node += 1) {
      if (!used[node] && (chosen === -1 || distance[node] < distance[chosen])) chosen = node;
    }
    used[chosen] = 1;
    total += distance[chosen];
    const [x, y] = points[chosen];
    for (let node = 0; node < size; node += 1) {
      if (!used[node]) {
        const cost = Math.abs(x - points[node][0]) + Math.abs(y - points[node][1]);
        distance[node] = Math.min(distance[node], cost);
      }
    }
  }
  return total;
}

const minCostConnectPoints = solve;
class Solution {
  minCostConnectPoints(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCostConnectPoints };
