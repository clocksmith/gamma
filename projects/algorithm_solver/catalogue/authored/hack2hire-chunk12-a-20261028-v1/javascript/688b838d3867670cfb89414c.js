"use strict";
// Hack2Hire 688b838d3867670cfb89414c (Merge N-ary Tree) over an INFERRED spec; qualification unknown.

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

function solve(root1, root2) {
  const [v1, k1] = parse(root1), [v2, k2] = parse(root2);
  if (!v1.length && !v2.length) return [];
  const value = (a, b) => (a >= 0 ? v1[a] : 0) + (b >= 0 ? v2[b] : 0);
  const pairs = [[v1.length ? 0 : -1, v2.length ? 0 : -1]], out = [value(pairs[0][0], pairs[0][1]), null];
  for (let head = 0; head < pairs.length; head++) {
    const [a, b] = pairs[head], ka = a >= 0 ? k1[a] : [], kb = b >= 0 ? k2[b] : [];
    for (let idx = 0; idx < Math.max(ka.length, kb.length); idx++) {
      const ca = idx < ka.length ? ka[idx] : -1, cb = idx < kb.length ? kb[idx] : -1;
      out.push(value(ca, cb));
      pairs.push([ca, cb]);
    }
    out.push(null);
  }
  while (out[out.length - 1] === null) out.pop();
  return out;
}

function mergeTrees(root1, root2) { return solve(root1, root2); }

module.exports = solve;
module.exports.mergeTrees = mergeTrees;
