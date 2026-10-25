'use strict';

// 2011. Final Value of Variable After Performing Operations (Easy).
// Specification: https://leetcode.com/problems/final-value-of-variable-after-performing-operations/description/
// O(n) time, O(1) space. The middle character identifies all four operations.
function solve(operations) {
  let value = 0;
  for (const operation of operations) value += operation[1] === '+' ? 1 : -1;
  return value;
}

const finalValueAfterOperations = solve;
class Solution {
  finalValueAfterOperations(operations) { return solve(operations); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, finalValueAfterOperations };
