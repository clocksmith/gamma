'use strict';

// 3243. Shortest Distance After Road Addition Queries I (Medium).
// Specification: https://leetcode.com/problems/shortest-distance-after-road-addition-queries-i/description/
function solve(n, queries) {
  const graph = Array.from({ length: n }, () => []);
  for (let i = 0; i + 1 < n; i++) graph[i].push(i + 1);
  function bfs() {
    const dist = new Array(n).fill(-1); dist[0] = 0;
    const queue = [0];
    for (let head = 0; head < queue.length; head++) {
      const u = queue[head];
      for (const v of graph[u]) if (dist[v] === -1) { dist[v] = dist[u] + 1; queue.push(v); }
    }
    return dist[n - 1];
  }
  const ans = [];
  for (const q of queries) {
    graph[q[0]].push(q[1]);
    ans.push(bfs());
  }
  return ans;
}
const shortestDistanceAfterQueries = solve;
class Solution { shortestDistanceAfterQueries(n, queries) { return solve(n, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, shortestDistanceAfterQueries };
