"use strict";
// Hack2Hire 69bc554c1cbff60a929be332 (Limit Tree Height by Deletions, variant 1) over an INFERRED spec; qualification unknown.

function solve(root, deletedIds) {
  const deleted = new Set(deletedIds);
  let best = 0;
  const nodes = [root], kept = [1];
  while (nodes.length) {
    const node = nodes.pop(), depth = kept.pop();
    if (depth > best) best = depth;
    for (const child of node.children) { nodes.push(child); kept.push(depth + (deleted.has(child.id) ? 0 : 1)); }
  }
  return best;
}

function maxHeightAfterDeletion(root, deletedIds) { return solve(root, deletedIds); }

module.exports = solve;
module.exports.maxHeightAfterDeletion = maxHeightAfterDeletion;
