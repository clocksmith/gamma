'use strict';

// 1405. Longest Happy String: take the most frequent available letter unless it would create three equal neighbors.
// O(a + b + c) time and O(a + b + c) space including the output; inputs are read-only.
function solve(a, b, c) {
  const counts = [[a, 'a'], [b, 'b'], [c, 'c']];
  const result = [];
  while (true) {
    counts.sort((x, y) => y[0] - x[0] || x[1].charCodeAt(0) - y[1].charCodeAt(0));
    let selected = 0;
    if (result.length >= 2 && result[result.length - 1] === counts[0][1] &&
        result[result.length - 2] === counts[0][1]) selected = 1;
    if (counts[selected][0] === 0) break;
    result.push(counts[selected][1]);
    counts[selected][0] -= 1;
  }
  return result.join('');
}

const longestDiverseString = solve;
class Solution {
  longestDiverseString(a, b, c) { return solve(a, b, c); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestDiverseString };
