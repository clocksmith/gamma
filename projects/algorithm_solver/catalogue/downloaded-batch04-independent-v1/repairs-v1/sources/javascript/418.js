'use strict';

// 418. Sentence Screen Fitting (Medium).
// Specification: https://leetcode.com/problems/sentence-screen-fitting/description/
function solve(sentence, rows, cols) {
  const text = sentence.join(' ') + ' ';
  let cursor = 0;
  for (let row = 0; row < rows; row++) {
    cursor += cols;
    if (text[cursor % text.length] === ' ') cursor++;
    else while (cursor > 0 && text[(cursor - 1) % text.length] !== ' ') cursor--;
  }
  return Math.floor(cursor / text.length);
}
const wordsTyping = solve;
class Solution { wordsTyping(sentence, rows, cols) { return solve(sentence, rows, cols); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordsTyping };
