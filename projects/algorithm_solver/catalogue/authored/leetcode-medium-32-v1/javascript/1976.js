'use strict';

// 1976. Number of Ways to Arrive at Destination: count shortest paths during Dijkstra relaxation.
// O(n^2 + e) time and O(n + e) auxiliary space; inputs are read-only.
function solve(n, roads) {
  const modulus = 1_000_000_007;
  const graph = Array.from({ length: n }, () => []);
  for (const [start, end, duration] of roads) {
    graph[start].push([end, duration]);
    graph[end].push([start, duration]);
  }
  const distances = new Array(n).fill(Infinity);
  const ways = new Array(n).fill(0);
  const settled = new Array(n).fill(false);
  distances[0] = 0;
  ways[0] = 1;

  // The declared n <= 200 bound permits an allocation-light dense selection.
  for (let count = 0; count < n; count += 1) {
    let node = -1;
    for (let candidate = 0; candidate < n; candidate += 1) {
      if (!settled[candidate] && (node === -1 || distances[candidate] < distances[node])) {
        node = candidate;
      }
    }
    if (node === -1 || distances[node] === Infinity) break;
    if (node === n - 1) break;
    settled[node] = true;
    for (const [neighbor, duration] of graph[node]) {
      const distance = distances[node] + duration;
      if (distance < distances[neighbor]) {
        distances[neighbor] = distance;
        ways[neighbor] = ways[node];
      } else if (distance === distances[neighbor]) {
        ways[neighbor] = (ways[neighbor] + ways[node]) % modulus;
      }
    }
  }
  return ways[n - 1];
}

const countPaths = solve;
class Solution {
  countPaths(n, roads) { return solve(n, roads); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPaths };
