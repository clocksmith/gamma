'use strict';

// 2492. Minimum Score of a Path Between Two Cities: find the lightest edge in the connected component containing city one.
// O(n + e) time and O(n + e) auxiliary space; inputs are read-only.
function solve(n, roads) {
  const graph = Array.from({ length: n + 1 }, () => []);
  for (const [left, right, distance] of roads) {
    graph[left].push([right, distance]);
    graph[right].push([left, distance]);
  }
  const seen = new Uint8Array(n + 1);
  seen[1] = 1;
  const stack = [1];
  let best = Infinity;
  while (stack.length) {
    const node = stack.pop();
    for (const [neighbor, distance] of graph[node]) {
      best = Math.min(best, distance);
      if (!seen[neighbor]) {
        seen[neighbor] = 1;
        stack.push(neighbor);
      }
    }
  }
  return best;
}

const minScore = solve;
class Solution {
  minScore(n, roads) { return solve(n, roads); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minScore };
