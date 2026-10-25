'use strict';

// 1319. Number of Operations to Make Network Connected: merge components with union by size and path halving.
// O(n + e * alpha(n)) time and O(n) auxiliary space; inputs are read-only.
function solve(n, connections) {
  if (connections.length < n - 1) return -1;
  const parent = Array.from({ length: n }, (_, index) => index);
  const size = new Array(n).fill(1);
  let components = n;

  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }

  for (const [left, right] of connections) {
    let leftRoot = find(left);
    let rightRoot = find(right);
    if (leftRoot === rightRoot) continue;
    if (size[leftRoot] < size[rightRoot]) [leftRoot, rightRoot] = [rightRoot, leftRoot];
    parent[rightRoot] = leftRoot;
    size[leftRoot] += size[rightRoot];
    components -= 1;
  }
  return components - 1;
}

const makeConnected = solve;
class Solution {
  makeConnected(n, connections) { return solve(n, connections); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeConnected };
