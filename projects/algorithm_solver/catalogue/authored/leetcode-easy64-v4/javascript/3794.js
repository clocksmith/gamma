'use strict';

// 3794. Reverse String Prefix (Easy).
// Specification: https://leetcode.com/problems/reverse-string-prefix/description/
// O(n) time and space; reverse exactly the first k lowercase ASCII characters.
function solve(s, k) {
  return s.slice(0, k).split('').reverse().join('') + s.slice(k);
}

const reversePrefix = solve;
class Solution {
  reversePrefix(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reversePrefix };
