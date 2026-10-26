'use strict';

// 1617. Count Subtrees With Max Distance Between Cities.
// Enumerate induced subsets of a tree and use all-pairs distances; O(n^2 * 2^n) time, O(n^2 + 2^n) space. Inputs are preserved.

function solve(n, edges) {
  const pairs = edges.map(([a, b]) => [a - 1, b - 1]);
  const graph = Array.from({ length: n }, () => []);
  for (const [a, b] of pairs) { graph[a].push(b); graph[b].push(a); }
  const distances = Array.from({ length: n }, () => Array(n).fill(-1));
  for (let start = 0; start < n; start += 1) {
    const queue = [start];
    distances[start][start] = 0;
    for (let head = 0; head < queue.length; head += 1) {
      const node = queue[head];
      for (const neighbor of graph[node]) {
        if (distances[start][neighbor] === -1) {
          distances[start][neighbor] = distances[start][node] + 1;
          queue.push(neighbor);
        }
      }
    }
  }
  const answer = Array(n - 1).fill(0), counts = new Uint8Array(1 << n);
  for (let mask = 1; mask < 1 << n; mask += 1) {
    counts[mask] = counts[mask >> 1] + (mask & 1);
    if (counts[mask] < 2) continue;
    let edgeCount = 0;
    for (const [a, b] of pairs) if ((mask & (1 << a)) && (mask & (1 << b))) edgeCount += 1;
    if (edgeCount !== counts[mask] - 1) continue;
    let diameter = 0;
    for (let a = 0; a < n; a += 1) {
      if (!(mask & (1 << a))) continue;
      for (let b = a + 1; b < n; b += 1) if (mask & (1 << b)) diameter = Math.max(diameter, distances[a][b]);
    }
    answer[diameter - 1] += 1;
  }
  return answer;
}

const countSubgraphsForEachDiameter = solve;
class Solution {
  countSubgraphsForEachDiameter(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubgraphsForEachDiameter };
