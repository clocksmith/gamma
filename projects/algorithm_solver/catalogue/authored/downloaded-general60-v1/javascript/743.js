'use strict';

// 743. Network Delay Time (Medium).
// Specification: https://leetcode.com/problems/network-delay-time/description/
function solve(times, n, k) {
  const graph = {};
  for (const [from, to, weight] of times) { if (!graph[from]) graph[from] = []; graph[from].push([to, weight]); }
  const dist = new Array(n + 1).fill(Infinity);
  dist[k] = 0;
  const visited = new Set();
  for (let step = 0; step < n; step++) {
    let node = -1; let best = Infinity;
    for (let i = 1; i <= n; i++) { if (!visited.has(i) && dist[i] < best) { best = dist[i]; node = i; } }
    if (node === -1) break;
    visited.add(node);
    for (const [to, weight] of (graph[node] || [])) { if (dist[node] + weight < dist[to]) dist[to] = dist[node] + weight; }
  }
  const answer = Math.max(...dist.slice(1));
  return answer === Infinity ? -1 : answer;
}
const networkDelayTime = solve;
class Solution { networkDelayTime(times, n, k) { return solve(times, n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, networkDelayTime };
