"use strict";
// Hack2Hire 69bd5fda1cbff60a929be96f (Implement Simplified Git Diff, level 1) over an INFERRED spec; qualification unknown.

function solve(lines1, lines2) {
  const count1 = new Map(), count2 = new Map(), where = new Map();
  for (const line of lines1) count1.set(line, (count1.get(line) || 0) + 1);
  lines2.forEach((line, j) => { count2.set(line, (count2.get(line) || 0) + 1); where.set(line, j); });
  for (let i = 0; i < lines1.length; i++) {
    if (count1.get(lines1[i]) === 1 && count2.get(lines1[i]) === 1) return [i, where.get(lines1[i])];
  }
  return [-1, -1];
}

function findUniqueCommonLine(lines1, lines2) { return solve(lines1, lines2); }

module.exports = solve;
module.exports.findUniqueCommonLine = findUniqueCommonLine;
