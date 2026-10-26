'use strict';

// 3767. Maximize Points After Choosing K Tasks.
// O(n log n) time and O(n) auxiliary space; choose at least k, not necessarily exactly k, first-technique tasks.
function solve(technique1, technique2, k) {
  const differences = technique1.map((value, index) => value - technique2[index]);
  differences.sort((left, right) => right - left);
  let answer = 0;
  for (const value of technique2) answer += value;
  for (let index = 0; index < differences.length; index += 1) {
    if (index < k || differences[index] > 0) answer += differences[index];
  }
  return answer;
}

const maxPoints = solve;
class Solution {
  maxPoints(technique1, technique2, k) { return solve(technique1, technique2, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxPoints };
