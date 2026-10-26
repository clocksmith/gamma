'use strict';

// 1392. Longest Happy Prefix.
// KMP prefix-function construction; O(n) time and O(n) space. Inputs are preserved.

function solve(s) {
  const border = Array(s.length).fill(0);
  for (let index = 1; index < s.length; index += 1) {
    let length = border[index - 1];
    while (length > 0 && s[index] !== s[length]) length = border[length - 1];
    if (s[index] === s[length]) length += 1;
    border[index] = length;
  }
  return s.length === 0 ? '' : s.slice(0, border[s.length - 1]);
}

const longestPrefix = solve;
class Solution {
  longestPrefix(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestPrefix };
