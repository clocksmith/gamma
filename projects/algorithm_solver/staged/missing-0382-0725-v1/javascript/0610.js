'use strict';

// 610. Triangle Judgement. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. triangle: x, y, z. Output: x, y, z, triangle.

function solve(triangle) {
  return triangle.map(({x, y, z}) => ({x, y, z, triangle: x + y > z && x + z > y && y + z > x ? 'Yes' : 'No'}));
}

const triangleJudgement = solve;
class Solution {
  triangleJudgement(triangle) { return solve(triangle); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, triangleJudgement };
