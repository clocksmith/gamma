"use strict";
// Hack2Hire 68dc2e1c9736cfa4e906240c (Level With Maximum Nodes in an N-ary Tree) over an INFERRED spec; qualification unknown.

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
  if (vals.length === 0) return 0;
  const level = new Array(vals.length).fill(0);
  level[0] = 1;
  const counts = [0, 0];
  for (let v = 0; v < vals.length; v++) { // breadth-first numbering: parents come before children
    counts[level[v]]++;
    for (const c of kids[v]) level[c] = level[v] + 1;
    if (kids[v].length && counts.length <= level[v] + 1) counts.push(0);
  }
  let best = 0, answer = 0;
  for (let lv = 1; lv < counts.length; lv++) if (counts[lv] > best) { best = counts[lv]; answer = lv; }
  return answer;
}

function levelWithMaxNodes(root) { return solve(root); }

module.exports = solve;
module.exports.levelWithMaxNodes = levelWithMaxNodes;
