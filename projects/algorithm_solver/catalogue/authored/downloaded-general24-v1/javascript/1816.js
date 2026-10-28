'use strict';

// 1816. Truncate Sentence (Easy).
// Specification: https://leetcode.com/problems/truncate-sentence/description/
function solve(s, k) {
  return s.split(' ').slice(0, k).join(' ');
}
const truncateSentence = solve;
class Solution { truncateSentence(s, k) { return solve(s, k); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, truncateSentence };
