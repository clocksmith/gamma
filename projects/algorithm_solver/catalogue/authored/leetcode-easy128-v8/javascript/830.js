'use strict';

// 830. Positions of Large Groups (Easy).
// Specification: https://leetcode.com/problems/positions-of-large-groups/description/
// O(n) time, O(1) auxiliary space excluding output; report inclusive bounds in order.
function solve(s) {
  const result = [];
  let start = 0;
  while (start < s.length) {
    let end = start + 1;
    while (end < s.length && s[end] === s[start]) end++;
    if (end - start >= 3) result.push([start, end - 1]);
    start = end;
  }
  return result;
}

const largeGroupPositions = solve;
class Solution {
  largeGroupPositions(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largeGroupPositions };
