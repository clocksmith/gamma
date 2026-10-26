'use strict';

// 1320. Minimum Distance to Type a Word Using Two Fingers: DP over the idle finger and last typed key; O(26*n) time and O(26) space.

function solve(word) {
  function distance(first, second) {
    if (first === 26) return 0;
    return Math.abs(Math.floor(first / 6) - Math.floor(second / 6)) + Math.abs(first % 6 - second % 6);
  }
  let best = Array(27).fill(Infinity);
  best[26] = 0;
  let previous = 26;
  for (const character of word) {
    const current = character.charCodeAt(0) - 65;
    const following = Array(27).fill(Infinity);
    for (let idle = 0; idle <= 26; idle += 1) {
      following[idle] = Math.min(following[idle], best[idle] + distance(previous, current));
      following[previous] = Math.min(following[previous], best[idle] + distance(idle, current));
    }
    best = following;
    previous = current;
  }
  return Math.min(...best);
}

const minimumDistance = solve;
class Solution {
  minimumDistance(word) { return solve(word); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDistance };
