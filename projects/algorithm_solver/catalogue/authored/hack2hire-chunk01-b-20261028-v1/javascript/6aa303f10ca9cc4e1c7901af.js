"use strict";
// Hack2Hire 6aa303f10ca9cc4e1c7901af (Directory Encryption Optimization, variant 1). Spec inferred by claude-opus-5-5 subagent 2026-10-28; qualification unknown.

function solve(root) {
  const order = [], stack = [root];
  while (stack.length) {
    const node = stack.pop();
    order.push(node);
    for (const child of node.directories) stack.push(child);
  }
  const info = new Map();
  for (let k = order.length - 1; k >= 0; k--) {
    const node = order[k];
    let cost = 0, files = node.files.length, clean = true;
    for (const f of node.files) {
      if (f.isEncrypted) cost++;
      else clean = false;
    }
    for (const child of node.directories) {
      const [childCost, childFiles, childClean] = info.get(child);
      info.delete(child);
      cost += childCost;
      files += childFiles;
      clean = clean && childClean;
    }
    if (files && clean) cost = 1;
    info.set(node, [cost, files, clean]);
  }
  return info.get(root)[0];
}

function minEncryptOperations(root) { return solve(root); }
module.exports = solve;
module.exports.minEncryptOperations = minEncryptOperations;
