'use strict';

// 2953. Count Complete Substrings.
// O(26*n) time, O(n+26) space. Exact-frequency counts are updated on entry and exit.
function solve(word, k) {
  const letters = Array.from(word, char => char.charCodeAt(0) - 97);
  let answer = 0;
  let start = 0;
  while (start < letters.length) {
    let stop = start + 1;
    while (stop < letters.length && Math.abs(letters[stop] - letters[stop - 1]) <= 2) stop += 1;
    const maximumDistinct = Math.min(26, Math.floor((stop - start) / k));
    for (let distinct = 1; distinct <= maximumDistinct; distinct += 1) {
      const width = distinct * k;
      const counts = new Int32Array(26);
      let exact = 0;
      for (let right = start; right < stop; right += 1) {
        const letter = letters[right];
        if (counts[letter] === k) exact -= 1;
        counts[letter] += 1;
        if (counts[letter] === k) exact += 1;
        if (right - start >= width) {
          const outgoing = letters[right - width];
          if (counts[outgoing] === k) exact -= 1;
          counts[outgoing] -= 1;
          if (counts[outgoing] === k) exact += 1;
        }
        if (right - start + 1 >= width && exact === distinct) answer += 1;
      }
    }
    start = stop;
  }
  return answer;
}

const countCompleteSubstrings = solve;
class Solution {
  countCompleteSubstrings(word, k) { return solve(word, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countCompleteSubstrings };
