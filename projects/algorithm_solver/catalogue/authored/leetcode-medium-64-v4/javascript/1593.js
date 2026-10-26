'use strict';

// 1593. Split a String Into the Max Number of Unique Substrings: backtrack over distinct pieces and prune by the remaining character budget.
// O(n * 2^n) time and O(n^2) auxiliary space including retained substring text; inputs are read-only.
function solve(s) {
  const used = new Set();
  let best = 0;
  function visit(start) {
    if (used.size + s.length - start <= best) return;
    if (start === s.length) {
      best = used.size;
      return;
    }
    for (let end = start + 1; end <= s.length; end += 1) {
      const word = s.slice(start, end);
      if (used.has(word)) continue;
      used.add(word);
      visit(end);
      used.delete(word);
    }
  }
  visit(0);
  return best;
}

const maxUniqueSplit = solve;
class Solution {
  maxUniqueSplit(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxUniqueSplit };
