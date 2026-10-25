'use strict';

// 2573. Find the String with LCP.
// O(n^2) time, O(n) space. Validation uses the full matrix without modifying it.
function solve(lcp) {
  const size = lcp.length;
  const letters = new Int32Array(size).fill(-1);
  let nextLetter = 0;
  for (let index = 0; index < size; index += 1) {
    if (letters[index] >= 0) continue;
    if (nextLetter === 26) return '';
    letters[index] = nextLetter;
    for (let other = index + 1; other < size; other += 1) {
      if (lcp[index][other] > 0) {
        if (letters[other] >= 0 && letters[other] !== nextLetter) return '';
        letters[other] = nextLetter;
      }
    }
    nextLetter += 1;
  }
  for (let first = size - 1; first >= 0; first -= 1) {
    for (let second = size - 1; second >= 0; second -= 1) {
      let expected = 0;
      if (letters[first] === letters[second]) {
        expected = 1;
        if (first + 1 < size && second + 1 < size) expected += lcp[first + 1][second + 1];
      }
      if (lcp[first][second] !== expected) return '';
    }
  }
  return Array.from(letters, letter => String.fromCharCode(97 + letter)).join('');
}

const findTheString = solve;
class Solution {
  findTheString(lcp) { return solve(lcp); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findTheString };
