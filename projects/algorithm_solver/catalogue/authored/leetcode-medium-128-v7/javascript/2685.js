'use strict';

// 2685. Count the Number of Complete Components: compare the total degree of each connected component with its complete-graph size.
// O(n + e) time and O(n + e) auxiliary space; inputs are read-only.
function solve(n, edges) {
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const seen = new Uint8Array(n);
  let complete = 0;
  for (let start = 0; start < n; start += 1) {
    if (seen[start]) continue;
    seen[start] = 1;
    const stack = [start];
    let size = 0;
    let degree = 0;
    while (stack.length) {
      const node = stack.pop();
      size += 1;
      degree += graph[node].length;
      for (const neighbor of graph[node]) {
        if (!seen[neighbor]) {
          seen[neighbor] = 1;
          stack.push(neighbor);
        }
      }
    }
    if (degree === size * (size - 1)) complete += 1;
  }
  return complete;
}

const countCompleteComponents = solve;
class Solution {
  countCompleteComponents(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCompleteComponents };
