'use strict';

// 686. Repeated String Match (Medium).
// Specification: https://leetcode.com/problems/repeated-string-match/description/
function solve(a, b) {
  let repeated = a;
  let count = 1;
  while (repeated.length < b.length) { repeated += a; count++; }
  if (repeated.includes(b)) return count;
  repeated += a;
  if (repeated.includes(b)) return count + 1;
  return -1;
}
const repeatedStringMatch = solve;
class Solution { repeatedStringMatch(a, b) { return solve(a, b); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, repeatedStringMatch };
