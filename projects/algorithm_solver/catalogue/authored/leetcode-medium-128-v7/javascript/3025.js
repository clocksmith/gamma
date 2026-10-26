'use strict';

// 3025. Find the Number of Ways to Place People I: sweep rightward from each upper-left point while excluding blocked lower-right choices.
// O(n * n) time and O(n) auxiliary space; inputs are read-only.
function solve(points) {
  const ordered = points.slice().sort((left, right) => left[0] - right[0] || right[1] - left[1]);
  let result = 0;
  for (let left = 0; left < ordered.length; left += 1) {
    const ceiling = ordered[left][1];
    let highest = -Infinity;
    for (let right = left + 1; right < ordered.length; right += 1) {
      const height = ordered[right][1];
      if (highest < height && height <= ceiling) {
        result += 1;
        highest = height;
      }
    }
  }
  return result;
}

const numberOfPairs = solve;
class Solution {
  numberOfPairs(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPairs };
