'use strict';

// 2316. Count Unreachable Pairs of Nodes in an Undirected Graph: join components and count pairs between each component and the uncounted remainder.
// O(n + e * alpha(n)) time and O(n) auxiliary space; inputs are read-only.
function solve(n, edges) {
  const parent = Array.from({ length: n }, (_, index) => index);
  const size = new Array(n).fill(1);
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  for (const [left, right] of edges) {
    let leftRoot = find(left);
    let rightRoot = find(right);
    if (leftRoot === rightRoot) continue;
    if (size[leftRoot] < size[rightRoot]) [leftRoot, rightRoot] = [rightRoot, leftRoot];
    parent[rightRoot] = leftRoot;
    size[leftRoot] += size[rightRoot];
  }
  let remaining = n;
  let answer = 0;
  for (let node = 0; node < n; node += 1) {
    if (parent[node] === node) {
      remaining -= size[node];
      answer += size[node] * remaining;
    }
  }
  return answer;
}

const countPairs = solve;
class Solution {
  countPairs(n, edges) { return solve(n, edges); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
