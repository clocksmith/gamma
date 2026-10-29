"use strict";
// Original Hack2Hire 6945a3fbe85c245612a9786c variant over an INFERRED specification; qualification unknown.
function solve(relationships) {
  const children = new Map(), reports = new Set();
  for (const row of relationships) {
    children.set(row[0], row.slice(1));
    for (let i = 1; i < row.length; i++) reports.add(row[i]);
  }
  const root = relationships.find((row) => !reports.has(row[0]))[0];
  const order = [], parent = new Map([[root, null]]), stack = [[root, 0]];
  while (stack.length) {
    const [name, depth] = stack.pop();
    order.push([name, depth]);
    const kids = children.get(name) || [];
    for (let i = kids.length - 1; i >= 0; i--) { parent.set(kids[i], name); stack.push([kids[i], depth + 1]); }
  }
  const below = new Map(order.map(([name]) => [name, 0]));
  for (let i = order.length - 1; i >= 0; i--) {
    const name = order[i][0], up = parent.get(name);
    if (up !== null) below.set(up, below.get(up) + below.get(name) + 1);
  }
  return order.map(([name, depth]) => "  ".repeat(depth) + name + " (" + below.get(name) + ")");
}
function printHierarchyWithCounts(relationships) { return solve(relationships); }
module.exports = solve;
module.exports.printHierarchyWithCounts = printHierarchyWithCounts;
