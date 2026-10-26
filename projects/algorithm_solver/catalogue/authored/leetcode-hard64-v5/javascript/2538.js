'use strict';

// 2538. Difference Between Maximum and Minimum Price Sum. Iterative tree DP for paths with one endpoint price excluded; O(n) time and O(n) space. Inputs are preserved.

function solve(n, edges, price) {
  const graph = Array.from({ length: n }, () => []);
  for (const [first, second] of edges) {
    graph[first].push(second);
    graph[second].push(first);
  }
  const parent = Array(n).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const neighbor of graph[node]) {
      if (neighbor === parent[node]) continue;
      parent[neighbor] = node;
      order.push(neighbor);
    }
  }
  const included = price.slice();
  const excluded = Array(n).fill(0);
  let answer = 0;
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index];
    for (const child of graph[node]) {
      if (parent[child] !== node) continue;
      answer = Math.max(answer, included[node] + excluded[child], excluded[node] + included[child]);
      included[node] = Math.max(included[node], price[node] + included[child]);
      excluded[node] = Math.max(excluded[node], price[node] + excluded[child]);
    }
  }
  return answer;
}

const maxOutput = solve;
class Solution {
  maxOutput(n, edges, price) { return solve(n, edges, price); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxOutput };
