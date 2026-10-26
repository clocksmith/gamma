'use strict';

// 3858. Minimum Bitwise OR From Grid.
// O(B mn) time and O(1) auxiliary space, B=17; greedily clear bits while preserving one allowed choice per row.
function solve(grid) {
  let answer = (1 << 17) - 1;
  for (let bit = 16; bit >= 0; bit -= 1) {
    const candidate = answer ^ (1 << bit);
    let possible = true;
    for (const row of grid) {
      let found = false;
      for (const value of row) {
        if ((value | candidate) === candidate) {
          found = true;
          break;
        }
      }
      if (!found) {
        possible = false;
        break;
      }
    }
    if (possible) answer = candidate;
  }
  return answer;
}

const minimumOR = solve;
class Solution {
  minimumOR(grid) { return solve(grid); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOR };
