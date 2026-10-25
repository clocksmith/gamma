'use strict';

// 1466. Reorder Routes to Make All Paths Lead to the City Zero: traverse the tree and count edges pointing away from zero.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(n, connections) {
  const graph = Array.from({ length: n }, () => []);
  for (const [start, end] of connections) {
    graph[start].push([end, 1]);
    graph[end].push([start, 0]);
  }
  const stack = [[0, -1]];
  let answer = 0;
  while (stack.length > 0) {
    const [node, parent] = stack.pop();
    for (const [neighbor, reversal] of graph[node]) {
      if (neighbor === parent) continue;
      answer += reversal;
      stack.push([neighbor, node]);
    }
  }
  return answer;
}

const minReorder = solve;
class Solution {
  minReorder(n, connections) { return solve(n, connections); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minReorder };
