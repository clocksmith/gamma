'use strict';

// 3021. Alice and Bob Playing Flower Game: count pairs whose total number of flowers is odd.
// O(1) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n, m) {
  return Math.ceil(n / 2) * Math.floor(m / 2) + Math.floor(n / 2) * Math.ceil(m / 2);
}

const flowerGame = solve;
class Solution {
  flowerGame(n, m) { return solve(n, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, flowerGame };
