"use strict";
// Hack2Hire 6976fe265ed12b33b05f1134 (Minimum Distance in N-ary Tree, level 2) over an INFERRED spec; qualification unknown.

function solve(root, groupA, groupB) {
  const neighbours = new Map();
  const nodes = [root], parents = [null];
  while (nodes.length) {
    const node = nodes.pop(), par = parents.pop();
    const adj = [];
    for (const child of node.children) { adj.push(child.val); nodes.push(child); parents.push(node.val); }
    if (par !== null) adj.push(par);
    neighbours.set(node.val, adj);
  }
  const targets = new Set(groupB), seen = new Set(groupA);
  let frontier = Array.from(seen), dist = 0;
  while (frontier.length) {
    for (const v of frontier) if (targets.has(v)) return dist;
    const following = [];
    for (const v of frontier) {
      for (const w of neighbours.get(v)) {
        if (!seen.has(w)) { seen.add(w); following.push(w); }
      }
    }
    frontier = following;
    dist++;
  }
  return -1;
}

function minSetDistance(root, groupA, groupB) { return solve(root, groupA, groupB); }

module.exports = solve;
module.exports.minSetDistance = minSetDistance;
