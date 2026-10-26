'use strict';

// 1233. Remove Sub-Folders from the Filesystem: sort a copy and reject paths inside the last retained parent.
// O(n * L * log(n + 1)) time and O(n + L) auxiliary space, where L is maximum path length; inputs are read-only.
function solve(folder) {
  const paths = folder.slice().sort();
  const result = [];
  for (const path of paths) {
    if (!result.length || !path.startsWith(result[result.length - 1] + '/')) {
      result.push(path);
    }
  }
  return result;
}

const removeSubfolders = solve;
class Solution {
  removeSubfolders(folder) { return solve(folder); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeSubfolders };
