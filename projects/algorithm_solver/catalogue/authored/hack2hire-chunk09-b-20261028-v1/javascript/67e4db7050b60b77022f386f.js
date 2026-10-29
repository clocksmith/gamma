"use strict";
// Hack2Hire 67e4db7050b60b77022f386f (Compress N-ary Tree) over an INFERRED spec; qualification unknown.

function solve(tree, compressedNodes) {
  const root = tree[0][0], gone = new Set(compressedNodes);
  gone.delete(root);
  const parent = new Map();
  for (const [value, children] of tree) for (const child of children) parent.set(child, value);
  const keptAncestor = new Map(), newChildren = new Map([[root, []]]), order = [root];
  for (let i = 1; i < tree.length; i++) {
    const value = tree[i][0], p = parent.get(value);
    const anchor = gone.has(p) ? keptAncestor.get(p) : p;
    keptAncestor.set(value, anchor);
    if (!gone.has(value)) {
      newChildren.get(anchor).push(value);
      newChildren.set(value, []);
      order.push(value);
    }
  }
  return order.map((value) => [value, newChildren.get(value)]);
}

function compressTree(tree, compressedNodes) { return solve(tree, compressedNodes); }

module.exports = solve;
module.exports.compressTree = compressTree;
