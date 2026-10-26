'use strict';

// 1324. Print Words Vertically: transpose word characters and remove only trailing padding.
// O(w * h) time and O(w * h) space for w words and maximum length h; inputs are read-only.
function solve(s) {
  const words = s.split(' ');
  let height = 0;
  for (const word of words) height = Math.max(height, word.length);
  const answer = [];
  for (let row = 0; row < height; row += 1) {
    const line = words.map(word => row < word.length ? word[row] : ' ').join('');
    answer.push(line.replace(/ +$/, ''));
  }
  return answer;
}

const printVertically = solve;
class Solution {
  printVertically(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, printVertically };
