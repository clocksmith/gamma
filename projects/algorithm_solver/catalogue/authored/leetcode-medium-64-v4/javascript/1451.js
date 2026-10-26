'use strict';

// 1451. Rearrange Words in a Sentence: stably order normalized words by length then capitalize the new first word.
// O(L + w log(w + 1)) time and O(L + w) auxiliary space; inputs are read-only.
function solve(text) {
  const words = text.toLowerCase().split(' ').map((word, index) => ({ word, index }));
  words.sort((a, b) => a.word.length - b.word.length || a.index - b.index);
  const sentence = words.map(item => item.word).join(' ');
  return sentence[0].toUpperCase() + sentence.slice(1);
}

const arrangeWords = solve;
class Solution {
  arrangeWords(text) { return solve(text); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, arrangeWords };
