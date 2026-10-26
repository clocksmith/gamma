'use strict';

// 1884. Egg Drop With 2 Eggs and N Floors: find the smallest triangular coverage that reaches the final floor.
// O(log(n + 1)) time and O(1) auxiliary space; inputs are read-only.
function solve(n) {
  let low = 1;
  let high = n;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (middle * (middle + 1) / 2 >= n) high = middle;
    else low = middle + 1;
  }
  return low;
}

const twoEggDrop = solve;
class Solution {
  twoEggDrop(n) { return solve(n); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, twoEggDrop };
