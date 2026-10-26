'use strict';

// 1925. Count Square Sum Triples (Easy).
// Specification: https://leetcode.com/problems/count-square-sum-triples/description/
// O(n^2) expected time, O(n) space; exact square membership counts both orders of the legs.
function solve(n) {
  const squares = new Set();
  for (let value = 1; value <= n; value++) squares.add(value * value);
  let result = 0;
  for (let first = 1; first <= n; first++) {
    for (let second = 1; second <= n; second++) {
      if (squares.has(first * first + second * second)) result++;
    }
  }
  return result;
}

const countTriples = solve;
class Solution {
  countTriples(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countTriples };
