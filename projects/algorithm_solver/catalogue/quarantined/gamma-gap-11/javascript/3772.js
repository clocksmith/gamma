'use strict';

// 3772. Maximum Subgraph Score in a Tree.
// O(n) time and O(n) space; iterative bottom-up and top-down rerooting.
function solve(n, edges, good) {
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const parent = new Int32Array(n).fill(-1);
  const order = [0];
  for (let head = 0; head < order.length; head += 1) {
    const node = order[head];
    for (const child of graph[node]) {
      if (child !== parent[node]) {
        parent[child] = node;
        order.push(child);
      }
    }
  }
  const down = good.map(value => 2 * value - 1);
  for (let index = n - 1; index > 0; index -= 1) {
    const node = order[index];
    down[parent[node]] += Math.max(0, down[node]);
  }
  const answer = down.slice();
  for (let index = 1; index < n; index += 1) {
    const node = order[index];
    answer[node] += Math.max(0, answer[parent[node]] - Math.max(0, down[node]));
  }
  return answer;
}

const maxSubgraphScore = solve;
class Solution {
  maxSubgraphScore(n, edges, good) { return solve(n, edges, good); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSubgraphScore };
