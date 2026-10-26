'use strict';

// 942. DI String Match (Easy).
// Specification: https://leetcode.com/problems/di-string-match/description/
// O(n) time and space; choose the smallest unused value for I and largest for D.
function solve(s) {
  let smallest = 0;
  let largest = s.length;
  const result = [];
  for (const direction of s) {
    if (direction === 'I') result.push(smallest++);
    else result.push(largest--);
  }
  result.push(smallest);
  return result;
}

const diStringMatch = solve;
class Solution {
  diStringMatch(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, diStringMatch };
