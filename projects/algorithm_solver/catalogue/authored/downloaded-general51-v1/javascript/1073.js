'use strict';

// 1073. Adding Two Negabinary Numbers (Medium).
// Specification: https://leetcode.com/problems/adding-two-negabinary-numbers/description/
function solve(arr1, arr2) {
  const result = [];
  let i = arr1.length - 1; let j = arr2.length - 1; let carry = 0;
  while (i >= 0 || j >= 0 || carry !== 0) {
    let total = carry;
    if (i >= 0) total += arr1[i--];
    if (j >= 0) total += arr2[j--];
    const digit = ((total % 2) + 2) % 2;
    result.push(digit);
    carry = -(total - digit) / 2;
  }
  while (result.length > 1 && result[result.length - 1] === 0) result.pop();
  return result.reverse();
}
const addNegabinary = solve;
class Solution { addNegabinary(arr1, arr2) { return solve(arr1, arr2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, addNegabinary };
