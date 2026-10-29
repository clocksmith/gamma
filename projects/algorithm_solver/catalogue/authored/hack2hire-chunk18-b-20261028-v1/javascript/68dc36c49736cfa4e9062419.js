"use strict";
// Hack2Hire 68dc36c49736cfa4e9062419 (Partition Array by Equivalence Function) over an INFERRED spec; qualification unknown.

function solve(nums, equivalentPairs) {
  const parent = new Map(), size = new Map();
  const find = (x) => {
    if (!parent.has(x)) { parent.set(x, x); size.set(x, 1); return x; }
    while (parent.get(x) !== x) {
      parent.set(x, parent.get(parent.get(x)));
      x = parent.get(x);
    }
    return x;
  };
  for (const [a, b] of equivalentPairs) {
    let ra = find(a), rb = find(b);
    if (ra !== rb) {
      if (size.get(ra) < size.get(rb)) [ra, rb] = [rb, ra];
      parent.set(rb, ra);
      size.set(ra, size.get(ra) + size.get(rb));
    }
  }
  const groups = [], where = new Map();
  for (const x of nums) {
    const root = find(x);
    let group = where.get(root);
    if (group === undefined) { group = []; where.set(root, group); groups.push(group); }
    group.push(x);
  }
  return groups;
}

function partitionByEquivalence(nums, equivalentPairs) { return solve(nums, equivalentPairs); }

module.exports = solve;
module.exports.partitionByEquivalence = partitionByEquivalence;
