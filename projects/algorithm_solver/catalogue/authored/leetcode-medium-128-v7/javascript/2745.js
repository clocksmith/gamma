'use strict';

// 2745. Construct the Longest New String: alternate AA and BB blocks and insert all AB blocks.
// O(1) time and O(1) auxiliary space; inputs are read-only.
function solve(x, y, z) {
  return 4 * Math.min(x, y) + 2 * z + (x !== y ? 2 : 0);
}

const longestString = solve;
class Solution {
  longestString(x, y, z) { return solve(x, y, z); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestString };
