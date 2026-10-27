'use strict';

// 402. Remove K Digits. Monotone digit stack; O(n) time.

function solve(num, k) {
  const stack = [];
  for (const digit of num) {
    while (k > 0 && stack.length > 0 && stack[stack.length - 1] > digit) {
      stack.pop(); k -= 1;
    }
    stack.push(digit);
  }
  if (k > 0) stack.length -= k;
  return stack.join('').replace(/^0+/, '') || '0';
}

const removeKdigits = solve;
class Solution {
  removeKdigits(num, k) { return solve(num, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeKdigits };
