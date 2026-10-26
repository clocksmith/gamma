'use strict';

// 2197. Replace Non-Coprime Numbers in Array. Stack of merged adjacent values; O(n log M) time and O(n) space, M bounds intermediate values. Inputs are preserved.

function solve(nums) {
  function gcd(first, second) {
    while (second !== 0) [first, second] = [second, first % second];
    return first;
  }
  const stack = [];
  for (const original of nums) {
    let value = original;
    while (stack.length > 0) {
      const common = gcd(stack[stack.length - 1], value);
      if (common === 1) break;
      value = (stack.pop() / common) * value;
    }
    stack.push(value);
  }
  return stack;
}

const replaceNonCoprimes = solve;
class Solution {
  replaceNonCoprimes(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, replaceNonCoprimes };
