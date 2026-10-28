'use strict';

// 609. Find Duplicate File in System (Medium).
// Specification: https://leetcode.com/problems/find-duplicate-file-in-system/description/
function solve(paths) {
  const groups = new Map();
  for (const path of paths) {
    const parts = path.split(' ');
    const directory = parts[0];
    for (let i = 1; i < parts.length; i++) {
      const openIndex = parts[i].indexOf('(');
      const name = parts[i].slice(0, openIndex);
      const content = parts[i].slice(openIndex + 1, -1);
      const full = directory + '/' + name;
      if (!groups.has(content)) groups.set(content, []);
      groups.get(content).push(full);
    }
  }
  const result = [];
  for (const group of groups.values()) { if (group.length > 1) result.push(group.slice().sort()); }
  result.sort((a, b) => a[0].localeCompare(b[0]));
  return result;
}
const findDuplicate = solve;
class Solution { findDuplicate(paths) { return solve(paths); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDuplicate };
