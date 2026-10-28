'use strict';

// 1079. Letter Tile Possibilities (Medium).
// Specification: https://leetcode.com/problems/letter-tile-possibilities/description/
function solve(tiles) {
  const counts = new Array(26).fill(0);
  for (const ch of tiles) counts[ch.charCodeAt(0) - 65]++;
  function dfs() {
    let total = 0;
    for (let i = 0; i < 26; i++) {
      if (counts[i] > 0) { counts[i]--; total += 1 + dfs(); counts[i]++; }
    }
    return total;
  }
  return dfs();
}
const numTilePossibilities = solve;
class Solution { numTilePossibilities(tiles) { return solve(tiles); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, numTilePossibilities };
