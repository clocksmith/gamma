'use strict';

// 1665. Minimum Initial Energy to Finish Tasks: greedy descending minimum-minus-actual ordering; O(n log n) time and O(n) space.

function solve(tasks) {
  const ordered = tasks.slice().sort((a, b) => (a[0] - a[1]) - (b[0] - b[1]));
  let energy = 0;
  let required = 0;
  for (const [actual, minimum] of ordered) {
    if (energy < minimum) {
      required += minimum - energy;
      energy = minimum;
    }
    energy -= actual;
  }
  return required;
}

const minimumEffort = solve;
class Solution {
  minimumEffort(tasks) { return solve(tasks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumEffort };
