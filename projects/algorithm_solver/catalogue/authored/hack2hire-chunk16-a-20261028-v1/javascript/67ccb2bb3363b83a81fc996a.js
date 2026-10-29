"use strict";
// Hack2Hire 67ccb2bb3363b83a81fc996a (Maximize Edge Sum in Graph) over an INFERRED spec; qualification unknown.

function solve(n, edges) {
  const degree = new Float64Array(n);
  for (const [a, b] of edges) { degree[a]++; degree[b]++; }
  degree.sort();
  let total = 0;
  for (let label = 1; label <= n; label++) total += label * degree[label - 1];
  return total;
}

function maximizeEdgeSum(n, edges) { return solve(n, edges); }

module.exports = solve;
module.exports.maximizeEdgeSum = maximizeEdgeSum;
