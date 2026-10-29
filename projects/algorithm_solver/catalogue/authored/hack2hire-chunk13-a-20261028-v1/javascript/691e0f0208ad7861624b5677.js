"use strict";
// Hack2Hire 691e0f0208ad7861624b5677 (Print Employee Org Chart) over an INFERRED spec; qualification unknown.

function solve(employees) {
  const reports = new Map(), names = new Map();
  let ceo = null;
  for (const [id, managerId, name] of employees) {
    names.set(id, name);
    if (id === managerId) ceo = id;
    else { let list = reports.get(managerId); if (!list) reports.set(managerId, list = []); list.push(id); }
  }
  const lines = [];
  const stack = [[ceo, 0]];
  while (stack.length) {
    const [id, depth] = stack.pop();
    lines.push("-".repeat(4 * depth) + names.get(id));
    const kids = reports.get(id);
    if (kids) for (let i = kids.length - 1; i >= 0; i--) stack.push([kids[i], depth + 1]); // first report printed first
  }
  return lines.join("\n");
}

function printOrgChart(employees) { return solve(employees); }

module.exports = solve;
module.exports.printOrgChart = printOrgChart;
