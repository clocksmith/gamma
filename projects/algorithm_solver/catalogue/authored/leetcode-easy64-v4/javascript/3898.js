'use strict';

// 3898. Find the Degree of Each Vertex (Easy).
// Specification: https://leetcode.com/problems/find-the-degree-of-each-vertex/description/
// O(n squared) time, O(n) output space; preserve the adjacency matrix and all rows.
function solve(matrix) {
  const result = [];
  for (const row of matrix) {
    let degree = 0;
    for (const value of row) degree += value;
    result.push(degree);
  }
  return result;
}

const findDegrees = solve;
class Solution {
  findDegrees(matrix) { return solve(matrix); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDegrees };
