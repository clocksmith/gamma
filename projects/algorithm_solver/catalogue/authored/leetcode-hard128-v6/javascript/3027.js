'use strict';

// 3027. Find the Number of Ways to Place People II.
// Sort by increasing x and decreasing y; sweep the highest blocking y for each upper-left corner. O(n^2) time, O(n) space. Inputs are preserved.

function solve(points) {
  const ordered = points.slice().sort((a, b) => a[0] - b[0] || b[1] - a[1]);
  let answer = 0;
  for (let index = 0; index < ordered.length; index += 1) {
    const upper = ordered[index][1];
    let blocked = -Infinity;
    for (let other = index + 1; other < ordered.length; other += 1) {
      const lower = ordered[other][1];
      if (blocked < lower && lower <= upper) { answer += 1; blocked = lower; }
    }
  }
  return answer;
}

const numberOfPairs = solve;
class Solution {
  numberOfPairs(points) { return solve(points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfPairs };
