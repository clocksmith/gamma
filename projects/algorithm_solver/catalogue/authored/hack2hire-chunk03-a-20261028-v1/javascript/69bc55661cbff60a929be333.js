"use strict";
// Hack2Hire 69bc55661cbff60a929be333 (Limit Tree Height by Deletions, variant 2) over an INFERRED spec; qualification unknown.

function solve(root, maxHeight) {
  const order = [], stack = [root];
  while (stack.length) {
    const node = stack.pop();
    order.push(node);
    for (const child of node.children) stack.push(child);
  }
  const height = new Map();
  let deletions = 0;
  for (let i = order.length - 1; i >= 0; i--) {
    const node = order[i];
    let h = 1;
    for (const child of node.children) h = Math.max(h, 1 + height.get(child.id));
    height.set(node.id, h);
    if (node !== root && h >= maxHeight) deletions++;
  }
  return deletions;
}

function minDeletionsForHeight(root, maxHeight) { return solve(root, maxHeight); }

module.exports = solve;
module.exports.minDeletionsForHeight = minDeletionsForHeight;
