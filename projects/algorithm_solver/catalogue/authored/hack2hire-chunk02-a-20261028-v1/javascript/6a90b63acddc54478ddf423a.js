"use strict";
// Hack2Hire 6a90b63acddc54478ddf423a (Largest Tree Root); INFERRED spec; qualification unknown.
function solve(relations) {
  if (relations.length === 0) return -1;
  const children = new Map(), isChild = new Set();
  for (const [child, parent] of relations) {
    if (!children.has(parent)) children.set(parent, []);
    children.get(parent).push(child); isChild.add(child);
  }
  let bestRoot = -1, bestSize = -1;
  for (const root of children.keys()) {
    if (isChild.has(root)) continue;
    let size = 0;
    const stack = [root];
    while (stack.length) { const node = stack.pop(); size++; const kids = children.get(node); if (kids) for (const k of kids) stack.push(k); }
    if (size > bestSize || (size === bestSize && root < bestRoot)) { bestRoot = root; bestSize = size; }
  }
  return bestRoot;
}
function largestTreeRoot(relations) { return solve(relations); }
module.exports = solve;
module.exports.largestTreeRoot = largestTreeRoot;
