"use strict";
// Original Hack2Hire 6941d017e79fe20cf9ff443f variant over an INFERRED specification; qualification unknown.
function solve(relationships) {
  const children = new Map(), reports = new Set();
  for (const row of relationships) {
    children.set(row[0], row.slice(1));
    for (let i = 1; i < row.length; i++) reports.add(row[i]);
  }
  const root = relationships.find((row) => !reports.has(row[0]))[0];
  const lines = [], stack = [[root, 0]];
  while (stack.length) {
    const [name, depth] = stack.pop();
    lines.push("  ".repeat(depth) + name);
    const kids = children.get(name) || [];
    for (let i = kids.length - 1; i >= 0; i--) stack.push([kids[i], depth + 1]);
  }
  return lines;
}
function printHierarchy(relationships) { return solve(relationships); }
module.exports = solve;
module.exports.printHierarchy = printHierarchy;
