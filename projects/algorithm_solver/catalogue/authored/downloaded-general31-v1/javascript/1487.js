'use strict';

// 1487. Making File Names Unique (Medium).
// Specification: https://leetcode.com/problems/making-file-names-unique/description/
function solve(names) {
  const used = new Set();
  const nextSuffix = new Map();
  const result = [];
  for (const name of names) {
    if (!used.has(name)) { used.add(name); nextSuffix.set(name, 1); result.push(name); continue; }
    let suffix = nextSuffix.get(name) || 1;
    while (used.has(name + '(' + suffix + ')')) suffix++;
    const unique = name + '(' + suffix + ')';
    used.add(unique);
    nextSuffix.set(name, suffix + 1);
    nextSuffix.set(unique, 1);
    result.push(unique);
  }
  return result;
}
const getFolderNames = solve;
class Solution { getFolderNames(names) { return solve(names); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getFolderNames };
