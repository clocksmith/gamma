'use strict';

// 2858. Minimum Edge Reversals So Every Node Is Reachable. Count reversals from one root and reroot across each edge; O(n) time and O(n) space. Inputs are preserved.

function solve(n, edges) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    graph[first].push([second, 0]);
    graph[second].push([first, 1]);
  }
  const parent = Array(n).fill(-1);
  const direction = Array(n).fill(0);
  const order = [0];
  let baseline = 0;
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const [neighbor, reversal] of graph[node]) {
      if (neighbor === parent[node]) continue;
      parent[neighbor] = node;
      direction[neighbor] = reversal;
      baseline += reversal;
      order.push(neighbor);
    }
  }
  const answer = Array(n).fill(0);
  answer[0] = baseline;
  for (let index = 1; index < order.length; index += 1) {
    const node = order[index];
    answer[node] = answer[parent[node]] + (direction[node] === 0 ? 1 : -1);
  }
  return answer;
}

const minEdgeReversals = solve;
class Solution {
  minEdgeReversals(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minEdgeReversals };
