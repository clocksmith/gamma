'use strict';

// 2039. The Time When the Network Becomes Idle: combine shortest round trips with the final resend strictly before the first reply.
// O(n + e) time and O(n + e) auxiliary space; inputs are read-only.
function solve(edges, patience) {
  const graph = Array.from({ length: patience.length }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const distance = new Int32Array(patience.length).fill(-1);
  distance[0] = 0;
  const queue = [0];
  for (let head = 0; head < queue.length; head += 1) {
    const node = queue[head];
    for (const neighbor of graph[node]) {
      if (distance[neighbor] === -1) {
        distance[neighbor] = distance[node] + 1;
        queue.push(neighbor);
      }
    }
  }
  let answer = 0;
  for (let node = 1; node < patience.length; node += 1) {
    const trip = 2 * distance[node];
    const lastSend = Math.floor((trip - 1) / patience[node]) * patience[node];
    answer = Math.max(answer, lastSend + trip + 1);
  }
  return answer;
}

const networkBecomesIdle = solve;
class Solution {
  networkBecomesIdle(edges, patience) { return solve(edges, patience); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, networkBecomesIdle };
