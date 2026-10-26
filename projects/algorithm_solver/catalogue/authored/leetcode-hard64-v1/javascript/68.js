'use strict';

// 68. Text Justification: greedy line packing with left-biased extra spaces.
// O(N + W) time and O(W) output space, W = output characters. Inputs are preserved.
function solve(words, maxWidth) {
  const lines = [];
  let left = 0;
  while (left < words.length) {
    let right = left;
    let letters = 0;
    while (right < words.length && letters + words[right].length + right - left <= maxWidth) {
      letters += words[right].length;
      right += 1;
    }
    const gaps = right - left - 1;
    if (right === words.length || gaps === 0) {
      lines.push(words.slice(left, right).join(' ').padEnd(maxWidth, ' '));
    } else {
      const width = Math.floor((maxWidth - letters) / gaps);
      const extra = (maxWidth - letters) % gaps;
      const pieces = [];
      for (let index = left; index < right; index += 1) {
        pieces.push(words[index]);
        if (index + 1 < right) pieces.push(' '.repeat(width + (index - left < extra ? 1 : 0)));
      }
      lines.push(pieces.join(''));
    }
    left = right;
  }
  return lines;
}

const fullJustify = solve;
class Solution {
  fullJustify(words, maxWidth) { return solve(words, maxWidth); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, fullJustify };
