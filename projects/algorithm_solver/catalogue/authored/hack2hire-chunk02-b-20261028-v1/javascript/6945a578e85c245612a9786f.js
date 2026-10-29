"use strict";
// Original Hack2Hire 6945a578e85c245612a9786f variant over an INFERRED specification; qualification unknown.
function solve(relationships, employee) {
  const manager = new Map();
  for (const row of relationships) for (let i = 1; i < row.length; i++) manager.set(row[i], row[0]);
  const chain = [employee];
  while (manager.has(chain[chain.length - 1])) chain.push(manager.get(chain[chain.length - 1]));
  return chain.reverse();
}
function reportChain(relationships, employee) { return solve(relationships, employee); }
module.exports = solve;
module.exports.reportChain = reportChain;
