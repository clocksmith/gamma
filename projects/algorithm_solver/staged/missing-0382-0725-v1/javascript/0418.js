'use strict';

// 418. Sentence Screen Fitting. Advance through a cyclic sentence without splitting words.

function solve(sentence, rows, cols) {
  const text = sentence.join(' ') + ' ';
  let position = 0;
  for (let row = 0; row < rows; row += 1) {
    position += cols;
    if (text[position % text.length] === ' ') position += 1;
    else while (position > 0 && text[(position - 1) % text.length] !== ' ') position -= 1;
  }
  return Math.floor(position / text.length);
}

const wordsTyping = solve;
class Solution {
  wordsTyping(sentence, rows, cols) { return solve(sentence, rows, cols); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordsTyping };
