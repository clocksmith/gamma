'use strict';

// 557. Reverse Words in a String III.

function solve(s) {
  return s.split(' ').map(word => Array.from(word).reverse().join('')).join(' ');
}

const reverseWords = solve;
class Solution {
  reverseWords(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseWords };
