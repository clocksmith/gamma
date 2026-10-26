'use strict';

// 3805. Count Caesar Cipher Pairs.
// O(S) expected time and O(S) space for S total ASCII characters; inputs are preserved.
function solve(words) {
  const frequencies = new Map();
  let answer = 0;
  for (const word of words) {
    const first = word.charCodeAt(0);
    const normalized = [];
    for (let index = 0; index < word.length; index += 1) {
      normalized.push(String.fromCharCode(97 + (word.charCodeAt(index) - first + 26) % 26));
    }
    const key = normalized.join('');
    const previous = frequencies.get(key) || 0;
    answer += previous;
    frequencies.set(key, previous + 1);
  }
  return answer;
}

const countPairs = solve;
class Solution {
  countPairs(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
