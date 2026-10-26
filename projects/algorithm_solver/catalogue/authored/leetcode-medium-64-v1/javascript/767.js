'use strict';

// 767. Reorganize String: fill alternating positions in descending frequency order.
// O(n + a log a) time and O(n + a) space for a <= 26 distinct letters; inputs are read-only.
function solve(s) {
  const counts = new Array(26).fill(0);
  for (let index = 0; index < s.length; index += 1) counts[s.charCodeAt(index) - 97] += 1;
  if (Math.max(...counts) > Math.floor((s.length + 1) / 2)) return '';
  const letters = Array.from({ length: 26 }, (_, index) => index);
  letters.sort((left, right) => counts[right] - counts[left] || left - right);
  const answer = new Array(s.length);
  let position = 0;
  for (const letter of letters) {
    for (let count = 0; count < counts[letter]; count += 1) {
      if (position >= s.length) position = 1;
      answer[position] = String.fromCharCode(97 + letter);
      position += 2;
    }
  }
  return answer.join('');
}

const reorganizeString = solve;
class Solution {
  reorganizeString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reorganizeString };
