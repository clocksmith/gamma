'use strict';

// 3887. Incremental Even-Weighted Cycle Queries.
// O((n+m) alpha(n)) time and O(n) space; parity union-find accepts only edges consistent with existing path parity.
function solve(n, edges) {
  const parent = Array.from({ length: n }, (_, index) => index);
  const sizes = Array(n).fill(1);
  const parity = Array(n).fill(0);
  function find(node) {
    let root = node;
    let total = 0;
    while (root !== parent[root]) {
      total ^= parity[root];
      root = parent[root];
    }
    const result = total;
    while (node !== root) {
      const following = parent[node];
      const edge = parity[node];
      parent[node] = root;
      parity[node] = total;
      total ^= edge;
      node = following;
    }
    return [root, result];
  }
  let answer = 0;
  for (const [left, right, weight] of edges) {
    let [rootLeft, valueLeft] = find(left);
    let [rootRight, valueRight] = find(right);
    const relation = valueLeft ^ valueRight ^ weight;
    if (rootLeft === rootRight) {
      if (relation === 0) answer += 1;
      continue;
    }
    if (sizes[rootLeft] < sizes[rootRight]) [rootLeft, rootRight] = [rootRight, rootLeft];
    parent[rootRight] = rootLeft;
    parity[rootRight] = relation;
    sizes[rootLeft] += sizes[rootRight];
    answer += 1;
  }
  return answer;
}

const maxEdges = solve;
class Solution {
  maxEdges(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxEdges };
