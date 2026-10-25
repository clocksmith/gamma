'use strict';

// 1887. Reduction Operations to Make the Array Elements Equal: sum the number of smaller distinct levels.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const values = [...nums].sort((left, right) => left - right);
  let levels = 0;
  let answer = 0;
  for (let index = 1; index < values.length; index += 1) {
    if (values[index] !== values[index - 1]) levels += 1;
    answer += levels;
  }
  return answer;
}

const reductionOperations = solve;
class Solution {
  reductionOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reductionOperations };
