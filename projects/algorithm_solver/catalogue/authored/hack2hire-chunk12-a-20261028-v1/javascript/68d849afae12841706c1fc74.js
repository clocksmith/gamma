"use strict";
// Hack2Hire 68d849afae12841706c1fc74 (Min Root-to-Leaf Path Sum of N-ary Tree) over an INFERRED spec; qualification unknown.

function parse(root) {
  // Values and child-index lists of a LeetCode N-ary level-order list; nodes are numbered breadth-first.
  if (root.length === 0) return [[], []];
  const vals = [root[0]], kids = [[]];
  let q = 0, i = 2;
  const n = root.length;
  while (i < n) {
    const group = kids[q];
    while (i < n && root[i] !== null) { group.push(vals.length); vals.push(root[i]); kids.push([]); i++; }
    i++; q++;
  }
  return [vals, kids];
}

function solve(root) {
  const [vals, kids] = parse(root);
  if (!vals.length) return 0;
  const total = vals.slice();
  let best = null;
  for (let v = 0; v < vals.length; v++) { // breadth-first numbering: a parent's total is final before its children
    if (kids[v].length) { for (const c of kids[v]) total[c] = total[v] + vals[c]; }
    else if (best === null || total[v] < best) best = total[v];
  }
  return best;
}

function minPathSum(root) { return solve(root); }

module.exports = solve;
module.exports.minPathSum = minPathSum;
