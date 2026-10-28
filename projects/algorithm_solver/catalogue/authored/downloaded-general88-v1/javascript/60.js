'use strict';

// 60. Permutation Sequence (Hard).
// Specification: https://leetcode.com/problems/permutation-sequence/description/
function solve(n, k) {
  const numbers = [];
  for (let i = 1; i <= n; i++) numbers.push(i);
  let factorial = 1;
  for (let i = 2; i < n; i++) factorial *= i;
  let remaining = k - 1;
  let result = '';
  for (let i = n; i >= 1; i--) {
    const index = Math.floor(remaining / factorial);
    result += String(numbers.splice(index, 1)[0]);
    remaining %= factorial;
    if (i > 1) factorial = Math.floor(factorial / (i - 1));
  }
  return result;
}
const getPermutation = solve;
class Solution { getPermutation(n, k) { return solve(n, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getPermutation };
