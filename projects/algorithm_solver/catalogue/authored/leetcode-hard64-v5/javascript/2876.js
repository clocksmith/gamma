'use strict';

// 2876. Count Visited Nodes in a Directed Graph. Peel directed tails, measure remaining cycles, then restore tail lengths; O(n) time and O(n) space. Inputs are preserved.

function solve(edges) {
  const size = edges.length;
  const indegree = Array(size).fill(0);
  for (const neighbor of edges) indegree[neighbor] += 1;
  const order = [];
  for (let node = 0; node < size; node += 1) if (indegree[node] === 0) order.push(node);
  for (let index = 0; index < order.length; index += 1) {
    const neighbor = edges[order[index]];
    indegree[neighbor] -= 1;
    if (indegree[neighbor] === 0) order.push(neighbor);
  }
  const answer = Array(size).fill(0);
  for (let start = 0; start < size; start += 1) {
    if (indegree[start] === 0) continue;
    const cycle = [];
    let node = start;
    while (indegree[node] > 0) {
      cycle.push(node);
      indegree[node] = 0;
      node = edges[node];
    }
    for (const member of cycle) answer[member] = cycle.length;
  }
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index];
    answer[node] = answer[edges[node]] + 1;
  }
  return answer;
}

const countVisitedNodes = solve;
class Solution {
  countVisitedNodes(edges) { return solve(edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countVisitedNodes };
