'use strict';

// 556. Next Greater Element III (Medium).
// Specification: https://leetcode.com/problems/next-greater-element-iii/description/
function solve(n) {
  const digits = String(n).split('').map(Number);
  let pivot = -1;
  for (let i = digits.length - 2; i >= 0; i--) { if (digits[i] < digits[i + 1]) { pivot = i; break; } }
  if (pivot === -1) return -1;
  for (let i = digits.length - 1; i > pivot; i--) {
    if (digits[i] > digits[pivot]) { const tmp = digits[i]; digits[i] = digits[pivot]; digits[pivot] = tmp; break; }
  }
  let left = pivot + 1; let right = digits.length - 1;
  while (left < right) { const tmp = digits[left]; digits[left] = digits[right]; digits[right] = tmp; left++; right--; }
  const result = Number(digits.join(''));
  return result > 2147483647 ? -1 : result;
}
const nextGreaterElement = solve;
class Solution { nextGreaterElement(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, nextGreaterElement };
