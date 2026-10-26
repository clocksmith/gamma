'use strict';

// 1519. Number of Nodes in the Sub-Tree With the Same Label: aggregate label frequencies in an iterative child-before-parent traversal.
// O(n) time and O(n) auxiliary space for a fixed 26-letter alphabet; inputs are read-only.
function solve(n, edges, labels) {
  const graph = Array.from({ length: n }, () => []);
  for (const [left, right] of edges) {
    graph[left].push(right);
    graph[right].push(left);
  }
  const parent = new Int32Array(n).fill(-1);
  const order = [0];
  for (let index = 0; index < order.length; index += 1) {
    const node = order[index];
    for (const neighbor of graph[node]) {
      if (neighbor !== parent[node]) {
        parent[neighbor] = node;
        order.push(neighbor);
      }
    }
  }
  const counts = new Uint32Array(26 * n);
  const answer = new Array(n).fill(0);
  for (let index = order.length - 1; index >= 0; index -= 1) {
    const node = order[index];
    const base = 26 * node;
    const letter = labels.charCodeAt(node) - 97;
    counts[base + letter] += 1;
    answer[node] = counts[base + letter];
    if (parent[node] !== -1) {
      const target = 26 * parent[node];
      for (let code = 0; code < 26; code += 1) counts[target + code] += counts[base + code];
    }
  }
  return answer;
}

const countSubTrees = solve;
class Solution {
  countSubTrees(n, edges, labels) { return solve(n, edges, labels); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubTrees };
