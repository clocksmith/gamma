'use strict';

// 605. Can Place Flowers (Easy).
// Specification: https://leetcode.com/problems/can-place-flowers/description/
// O(m) time, O(1) space; greedily plant using virtual previous occupancy; preserve flowerbed.
function solve(flowerbed, n) {
  let remaining = n;
  let previous = 0;
  for (let index = 0; index < flowerbed.length; index++) {
    if (remaining <= 0) return true;
    const next = index + 1 < flowerbed.length ? flowerbed[index + 1] : 0;
    if (flowerbed[index] === 0 && previous === 0 && next === 0) {
      remaining--;
      previous = 1;
    } else {
      previous = flowerbed[index];
    }
  }
  return remaining <= 0;
}

const canPlaceFlowers = solve;
class Solution {
  canPlaceFlowers(flowerbed, n) { return solve(flowerbed, n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canPlaceFlowers };
