'use strict';

// 1662. Check If Two String Arrays are Equivalent (Easy).
// Specification: https://leetcode.com/problems/check-if-two-string-arrays-are-equivalent/description/
// O(total characters) time, O(1) space; compare nonempty input pieces without joining.
function solve(word1, word2) {
  let firstWord = 0;
  let secondWord = 0;
  let firstCharacter = 0;
  let secondCharacter = 0;
  while (firstWord < word1.length && secondWord < word2.length) {
    if (word1[firstWord][firstCharacter] !== word2[secondWord][secondCharacter]) return false;
    firstCharacter++;
    secondCharacter++;
    if (firstCharacter === word1[firstWord].length) {
      firstWord++;
      firstCharacter = 0;
    }
    if (secondCharacter === word2[secondWord].length) {
      secondWord++;
      secondCharacter = 0;
    }
  }
  return firstWord === word1.length && secondWord === word2.length;
}

const arrayStringsAreEqual = solve;
class Solution {
  arrayStringsAreEqual(word1, word2) { return solve(word1, word2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrayStringsAreEqual };
