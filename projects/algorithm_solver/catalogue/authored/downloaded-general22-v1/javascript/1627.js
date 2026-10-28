'use strict';

// 1627. Graph Connectivity With Threshold (Medium).
// Specification: https://leetcode.com/problems/graph-connectivity-with-threshold/description/
function solve(n, threshold, queries) {
  const parent = [];
  for (let i = 0; i <= n; i++) parent.push(i);
  function find(x) { while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; } return x; }
  function union(a, b) { parent[find(a)] = find(b); }
  for (let divisor = threshold + 1; divisor <= n; divisor++) {
    for (let multiple = divisor * 2; multiple <= n; multiple += divisor) union(divisor, multiple);
  }
  return queries.map(([a, b]) => find(a) === find(b));
}
const areConnected = solve;
class Solution { areConnected(n, threshold, queries) { return solve(n, threshold, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, areConnected };
