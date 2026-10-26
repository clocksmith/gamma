'use strict';

// 2171. Removing Minimum Number of Magic Beans: choose the retained nonempty bag size from a sorted copy.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(beans) {
  const ordered = beans.slice().sort((left, right) => left - right);
  let total = 0;
  for (const value of ordered) total += value;
  let best = total;
  for (let index = 0; index < ordered.length; index += 1) {
    best = Math.min(best, total - ordered[index] * (ordered.length - index));
  }
  return best;
}

const minimumRemoval = solve;
class Solution {
  minimumRemoval(beans) { return solve(beans); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumRemoval };
