"use strict";
// Hack2Hire 6aa304120ca9cc4e1c7901b3 (Directory Encryption Optimization, variant 2). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(root) {
  const order = [], stack = [root];
  while (stack.length) {
    const node = stack.pop();
    order.push(node);
    for (const child of node.directories) stack.push(child);
  }
  const cost = new Map();
  for (let k = order.length - 1; k >= 0; k--) {
    const node = order[k];
    let keepOff = 0, keepOn = 0;
    for (const f of node.files) {
      if (f.isEncrypted) keepOff++;
      else keepOn++;
    }
    for (const child of node.directories) {
      const [off, on] = cost.get(child);
      cost.delete(child);
      keepOff += off;
      keepOn += on;
    }
    cost.set(node, [Math.min(keepOff, 1 + keepOn), Math.min(keepOn, 1 + keepOff)]);
  }
  return cost.get(root)[0];
}

function minStateOperations(root) { return solve(root); }
module.exports = solve;
module.exports.minStateOperations = minStateOperations;
