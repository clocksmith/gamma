'use strict';

// 2379. Minimum Recolors to Get K Consecutive Black Blocks (Easy).
// Specification: https://leetcode.com/problems/minimum-recolors-to-get-k-consecutive-black-blocks/description/
// O(n) time, O(1) space; minimize white blocks in a k-wide sliding window.
function solve(blocks, k) {
  let whites = 0;
  for (let index = 0; index < k; index++) {
    if (blocks[index] === 'W') whites++;
  }
  let best = whites;
  for (let index = k; index < blocks.length; index++) {
    if (blocks[index] === 'W') whites++;
    if (blocks[index - k] === 'W') whites--;
    best = Math.min(best, whites);
  }
  return best;
}

const minimumRecolors = solve;
class Solution {
  minimumRecolors(blocks, k) { return solve(blocks, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumRecolors };
