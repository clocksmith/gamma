'use strict';

// 3796. Find Maximum Value in a Constrained Sequence.
// O(n + r) time and O(n) space; two passes compute the greatest feasible Lipschitz envelope.
function solve(n, restrictions, diff) {
  const bound = Array(n).fill(Infinity);
  bound[0] = 0;
  for (const [index, maximum] of restrictions) bound[index] = Math.min(bound[index], maximum);
  for (let index = 1; index < n; index += 1) bound[index] = Math.min(bound[index], bound[index - 1] + diff[index - 1]);
  for (let index = n - 2; index >= 0; index -= 1) bound[index] = Math.min(bound[index], bound[index + 1] + diff[index]);
  let answer = 0;
  for (const value of bound) answer = Math.max(answer, value);
  return answer;
}

const findMaxVal = solve;
class Solution {
  findMaxVal(n, restrictions, diff) { return solve(n, restrictions, diff); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxVal };
