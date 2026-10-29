"use strict";
// Hack2Hire 696eb8a4920c39311a3992be (Minimum Distance in N-ary Tree, level 1) over an INFERRED spec; qualification unknown.

function solve(root, p, q) {
  const parent = new Map(), depth = new Map();
  const nodes = [root], parents = [null], depths = [0];
  while (nodes.length) {
    const node = nodes.pop(), par = parents.pop(), d = depths.pop();
    parent.set(node.val, par);
    depth.set(node.val, d);
    for (const child of node.children) { nodes.push(child); parents.push(node.val); depths.push(d + 1); }
  }
  let x = p, y = q, dist = 0;
  while (depth.get(x) > depth.get(y)) { x = parent.get(x); dist++; }
  while (depth.get(y) > depth.get(x)) { y = parent.get(y); dist++; }
  while (x !== y) { x = parent.get(x); y = parent.get(y); dist += 2; }
  return dist;
}

function treeDistance(root, p, q) { return solve(root, p, q); }

module.exports = solve;
module.exports.treeDistance = treeDistance;
