"use strict";

function collect(root) {
  if (Array.isArray(root)) {
    const s = new Set();
    for (let i = 0; i < root.length; i++) if (root[i] !== null) s.add(root[i]);
    return s;
  }
  const s = new Set();
  const stack = [root];
  while (stack.length > 0) {
    const node = stack.pop();
    if (node !== null && node !== undefined) {
      s.add(node.val);
      stack.push(node.left);
      stack.push(node.right);
    }
  }
  return s;
}

function solve(root1, root2, target) {
  const s1 = collect(root1);
  const s2 = collect(root2);
  for (const y of s2) {
    if (s1.has(target - y)) return true;
  }
  return false;
}

function twoSumBSTs(root1, root2, target) {
  return solve(root1, root2, target);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.twoSumBSTs = twoSumBSTs;
