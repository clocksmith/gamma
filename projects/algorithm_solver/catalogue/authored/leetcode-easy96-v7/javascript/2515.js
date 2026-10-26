'use strict';

// 2515. Shortest Distance to Target String in a Circular Array (Easy).
// Specification: https://leetcode.com/problems/shortest-distance-to-target-string-in-a-circular-array/description/
// O(total compared characters) time, O(1) space; minimize clockwise/counterclockwise distance; preserve words.
function solve(words, target, startIndex) {
  let best = words.length;
  for (let index = 0; index < words.length; index++) {
    if (words[index] !== target) continue;
    const distance = Math.abs(index - startIndex);
    best = Math.min(best, distance, words.length - distance);
  }
  return best === words.length ? -1 : best;
}

const closetTarget = solve;
class Solution {
  closetTarget(words, target, startIndex) { return solve(words, target, startIndex); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, closetTarget };
