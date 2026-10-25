'use strict';

// 1880. Check if Word Equals Summation of Two Words (Easy).
// Specification: https://leetcode.com/problems/check-if-word-equals-summation-of-two-words/description/
// O(total characters) time, O(1) space. Letters a-j encode decimal digits.
function solve(firstWord, secondWord, targetWord) {
  function wordValue(word) {
    let value = 0;
    for (const character of word) {
      value = value * 10 + character.charCodeAt(0) - 97;
    }
    return value;
  }
  return wordValue(firstWord) + wordValue(secondWord) === wordValue(targetWord);
}

const isSumEqual = solve;
class Solution {
  isSumEqual(firstWord, secondWord, targetWord) { return solve(firstWord, secondWord, targetWord); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isSumEqual };
