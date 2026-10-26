'use strict';

// 2030. Smallest K-Length Subsequence With Occurrences of a Letter. Quota-aware monotonic stack; O(n) time and O(k) space. Inputs are preserved.

function solve(s, k, letter, repetition) {
  let remaining = 0;
  for (const character of s) if (character === letter) remaining += 1;
  let needed = repetition;
  const stack = [];
  for (let index = 0; index < s.length; index += 1) {
    const character = s[index];
    while (stack.length > 0 && stack[stack.length - 1] > character
        && stack.length - 1 + s.length - index >= k
        && (stack[stack.length - 1] !== letter || remaining > needed)) {
      if (stack.pop() === letter) needed += 1;
    }
    if (stack.length < k) {
      if (character === letter) {
        stack.push(character);
        needed -= 1;
      } else if (k - stack.length > needed) {
        stack.push(character);
      }
    }
    if (character === letter) remaining -= 1;
  }
  return stack.join('');
}

const smallestSubsequence = solve;
class Solution {
  smallestSubsequence(s, k, letter, repetition) { return solve(s, k, letter, repetition); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestSubsequence };
