"use strict";
// Hack2Hire 684ba2bf4023c4f502877de9 (Find Defendency Bottleneck) over an INFERRED spec; qualification unknown.

function solve(n, edges) {
  const out = Array.from({length: n}, () => []), indegree = new Int32Array(n);
  for (const [u, v] of edges) { out[u].push(v); indegree[v]++; }
  let frontier = [];
  for (let v = 0; v < n; v++) if (indegree[v] === 0) frontier.push(v);
  const bottlenecks = [];
  while (frontier.length) {
    if (frontier.length === 1) bottlenecks.push(frontier[0]);
    const following = [];
    for (const u of frontier) for (const v of out[u]) if (--indegree[v] === 0) following.push(v);
    frontier = following;
  }
  return bottlenecks;
}

function findBottlenecks(n, edges) { return solve(n, edges); }

module.exports = solve;
module.exports.findBottlenecks = findBottlenecks;
