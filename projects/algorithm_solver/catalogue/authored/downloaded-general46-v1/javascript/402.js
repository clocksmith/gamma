'use strict';

// 402. Remove K Digits (Medium).
// Specification: https://leetcode.com/problems/remove-k-digits/description/
function solve(num, k) {
  const stack = [];
  for (const ch of num) {
    while (k > 0 && stack.length > 0 && stack[stack.length - 1] > ch) { stack.pop(); k--; }
    stack.push(ch);
  }
  while (k > 0) { stack.pop(); k--; }
  let result = stack.join('').replace(/^0+/, '');
  return result === '' ? '0' : result;
}
const removeKdigits = solve;
class Solution { removeKdigits(num, k) { return solve(num, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeKdigits };
