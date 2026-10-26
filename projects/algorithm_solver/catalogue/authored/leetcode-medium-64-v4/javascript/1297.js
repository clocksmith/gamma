'use strict';

// 1297. Maximum Number of Occurrences of a Substring: count valid minimum-length windows since extending a substring cannot increase its frequency.
// O(n * minSize) time and O(n * minSize) auxiliary space including substring keys; inputs are read-only.
function solve(s, maxLetters, minSize, maxSize) {
  const counts = new Int32Array(26);
  const frequency = new Map();
  let distinct = 0;
  let best = 0;
  for (let right = 0; right < s.length; right += 1) {
    const index = s.charCodeAt(right) - 97;
    if (counts[index] === 0) distinct += 1;
    counts[index] += 1;
    if (right >= minSize) {
      const outgoing = s.charCodeAt(right - minSize) - 97;
      counts[outgoing] -= 1;
      if (counts[outgoing] === 0) distinct -= 1;
    }
    if (right + 1 >= minSize && distinct <= maxLetters) {
      const word = s.slice(right - minSize + 1, right + 1);
      const count = (frequency.get(word) || 0) + 1;
      frequency.set(word, count);
      best = Math.max(best, count);
    }
  }
  return best;
}

const maxFreq = solve;
class Solution {
  maxFreq(s, maxLetters, minSize, maxSize) { return solve(s, maxLetters, minSize, maxSize); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxFreq };
