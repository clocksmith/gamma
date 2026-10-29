"use strict";
// Hack2Hire 695d3f8768e2c0dd046c4aa3 (Find Bad GPU Nodes) over an INFERRED spec; qualification unknown.

function solve(n, badNodes) {
  const flag = new Uint8Array(n);
  for (const b of badNodes) flag[b] = 1;
  let calls = 0;
  const test = (lo, hi) => { // simulated TestServer.test over nodes lo..hi-1
    calls += 1;
    for (let i = lo; i < hi; i++) if (flag[i]) return false;
    return true;
  };
  const bad = [], ranges = [[0, n]];
  while (ranges.length) {
    const [lo, hi] = ranges.pop();
    if (test(lo, hi)) continue;
    if (hi - lo === 1) { bad.push(lo); continue; }
    const mid = Math.floor((lo + hi) / 2);
    ranges.push([mid, hi], [lo, mid]);
  }
  return [bad, calls];
}

function findBadNodes(n, badNodes) { return solve(n, badNodes); }

module.exports = solve;
module.exports.findBadNodes = findBadNodes;
