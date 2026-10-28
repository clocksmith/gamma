'use strict';

// 1243. Array Transformation (Easy).
// Specification: https://leetcode.com/problems/array-transformation/description/
function solve(arr) {
  let current = arr.slice();
  while (true) {
    const next = current.slice();
    for (let i = 1; i < current.length - 1; i++) {
      if (current[i] < current[i - 1] && current[i] < current[i + 1]) next[i] = current[i] + 1;
      else if (current[i] > current[i - 1] && current[i] > current[i + 1]) next[i] = current[i] - 1;
    }
    let changed = false;
    for (let i = 0; i < current.length; i++) { if (next[i] !== current[i]) { changed = true; break; } }
    current = next;
    if (!changed) break;
  }
  return current;
}
const transformArray = solve;
class Solution { transformArray(arr) { return solve(arr); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, transformArray };
