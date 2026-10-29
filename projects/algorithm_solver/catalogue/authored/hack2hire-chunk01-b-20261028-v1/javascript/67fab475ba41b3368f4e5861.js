"use strict";
// Hack2Hire 67fab475ba41b3368f4e5861 (Find Destination Node, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(edges, start) {
  const successor = new Map();
  for (const [u, v] of edges) successor.set(u, v);
  const seen = new Set();
  let node = start;
  while (successor.has(node)) {
    if (seen.has(node)) return -1;
    seen.add(node);
    node = successor.get(node);
  }
  return node;
}

function findDestinationNode(edges, start) { return solve(edges, start); }
module.exports = solve;
module.exports.findDestinationNode = findDestinationNode;
