'use strict';

// 1888. Minimum Number of Flips to Make the Binary String Alternating: slide an n-character window over the implicit doubled string.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(s) {
  const length = s.length;
  let mismatches = 0;
  let best = length;
  for (let right = 0; right < 2 * length - 1; right += 1) {
    if (s.charCodeAt(right % length) - 48 !== right % 2) mismatches += 1;
    if (right >= length) {
      const left = right - length;
      if (s.charCodeAt(left % length) - 48 !== left % 2) mismatches -= 1;
    }
    if (right >= length - 1) best = Math.min(best, mismatches, length - mismatches);
  }
  return best;
}

const minFlips = solve;
class Solution {
  minFlips(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minFlips };
