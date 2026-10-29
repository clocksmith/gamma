"use strict";
// Original Hack2Hire 6945ada2e85c245612a97880 variant over an INFERRED specification; qualification unknown.
function solve(relationships, first, second) {
  const manager = new Map();
  for (const row of relationships) for (let i = 1; i < row.length; i++) manager.set(row[i], row[0]);
  const depth = (name) => { let d = 0; while (manager.has(name)) { name = manager.get(name); d++; } return d; };
  let a = first, b = second, da = depth(a), db = depth(b);
  while (da > db) { a = manager.get(a); da--; }
  while (db > da) { b = manager.get(b); db--; }
  while (a !== b) { a = manager.get(a); b = manager.get(b); }
  return a;
}
function closestCommonManager(relationships, first, second) { return solve(relationships, first, second); }
module.exports = solve;
module.exports.closestCommonManager = closestCommonManager;
