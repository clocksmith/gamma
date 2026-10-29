"use strict";
// Hack2Hire 67cb459e9db31a8671abf92c (Find Lowest Common Manager) over an INFERRED spec; qualification unknown.

function solve(hierarchy, employee1, employee2) {
  const reports = new Map();
  for (const [name, direct] of hierarchy) reports.set(name, direct);
  const root = hierarchy[0][0];
  const parent = new Map([[root, null]]), depth = new Map([[root, 0]]), queue = [root];
  for (let i = 0; i < queue.length; i++) { // iterative breadth-first pass: the tree may be 1e5 deep
    const x = queue[i];
    for (const child of reports.get(x)) {
      parent.set(child, x);
      depth.set(child, depth.get(x) + 1);
      queue.push(child);
    }
  }
  let a = employee1, b = employee2;
  while (depth.get(a) > depth.get(b)) a = parent.get(a);
  while (depth.get(b) > depth.get(a)) b = parent.get(b);
  while (a !== b) { a = parent.get(a); b = parent.get(b); }
  return a;
}

function findLowestCommonManager(hierarchy, employee1, employee2) { return solve(hierarchy, employee1, employee2); }

module.exports = solve;
module.exports.findLowestCommonManager = findLowestCommonManager;
