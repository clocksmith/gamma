'use strict';

// 1739. Building Boxes.
// Fill complete triangular layers, then extend the last floor row; O(cube_root(n)) time, O(1) space.

function solve(n) {
  let height = 0, floor = 0, volume = 0;
  while (volume + floor + height + 1 <= n) {
    height += 1;
    floor += height;
    volume += floor;
  }
  let extra = 0;
  while (volume < n) { extra += 1; volume += extra; }
  return floor + extra;
}

const minimumBoxes = solve;
class Solution {
  minimumBoxes(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumBoxes };
