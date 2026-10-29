"use strict";
// Hack2Hire 67fac1b6ba41b3368f4e5865 (Find Destination Node, variant 2). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(edges, start) {
  const adjacency = new Map();
  for (const [u, v] of edges) {
    if (!adjacency.has(u)) adjacency.set(u, []);
    adjacency.get(u).push(v);
  }
  const seen = new Set([start]), queue = [start], sinks = [];
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head];
    if (!adjacency.has(node)) {
      sinks.push(node);
      continue;
    }
    for (const next of adjacency.get(node)) {
      if (!seen.has(next)) {
        seen.add(next);
        queue.push(next);
      }
    }
  }
  return sinks.sort((a, b) => a - b);
}

function findDestinationNodes(edges, start) { return solve(edges, start); }
module.exports = solve;
module.exports.findDestinationNodes = findDestinationNodes;
