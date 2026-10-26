'use strict';

// 1668. Maximum Repeating Substring (Easy).
// Specification: https://leetcode.com/problems/maximum-repeating-substring/description/
// O(n * m) time, O(n) space; n=len(sequence), m=len(word).
function solve(sequence, word) {
  const length = word.length;
  const repetitions = new Array(sequence.length + 1).fill(0);
  let result = 0;
  for (let end = length; end <= sequence.length; end++) {
    if (sequence.startsWith(word, end - length)) {
      repetitions[end] = repetitions[end - length] + 1;
      result = Math.max(result, repetitions[end]);
    }
  }
  return result;
}

const maxRepeating = solve;
class Solution {
  maxRepeating(sequence, word) { return solve(sequence, word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxRepeating };
