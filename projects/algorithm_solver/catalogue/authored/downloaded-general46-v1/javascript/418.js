'use strict';

// 418. Sentence Screen Fitting (Medium).
// Specification: https://leetcode.com/problems/sentence-screen-fitting/description/
function solve(sentence, rows, cols) {
  let wordIndex = 0; let completed = 0;
  for (let row = 0; row < rows; row++) {
    let remaining = cols;
    while (remaining >= sentence[wordIndex].length) {
      remaining -= sentence[wordIndex].length + 1;
      wordIndex++;
      if (wordIndex === sentence.length) { wordIndex = 0; completed++; }
    }
  }
  return completed;
}
const wordsTyping = solve;
class Solution { wordsTyping(sentence, rows, cols) { return solve(sentence, rows, cols); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordsTyping };
