'use strict';

// 1836. Remove Sub-Folders from the Filesystem (Medium).
// Specification: https://leetcode.com/problems/remove-sub-folders-from-the-filesystem/description/
function solve(folder) {
  const sorted = folder.slice().sort();
  const result = [];
  for (const path of sorted) {
    if (result.length === 0 || !path.startsWith(result[result.length - 1] + '/')) result.push(path);
  }
  return result;
}
const removeSubfolders = solve;
class Solution { removeSubfolders(folder) { return solve(folder); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeSubfolders };
