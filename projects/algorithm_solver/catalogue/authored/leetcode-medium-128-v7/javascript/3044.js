'use strict';

// 3044. Most Frequent Prime: count straight-line decimal numbers and test each distinct candidate for primality once.
// O(r * c * L + u * sqrt(M)) time and O(u) auxiliary space, where L is the maximum ray length; inputs are read-only.
function solve(mat) {
  const rows = mat.length;
  const columns = mat[0].length;
  const counts = new Map();
  for (let row = 0; row < rows; row += 1) {
    for (let column = 0; column < columns; column += 1) {
      for (let dr = -1; dr <= 1; dr += 1) {
        for (let dc = -1; dc <= 1; dc += 1) {
          if (dr === 0 && dc === 0) continue;
          let nr = row;
          let nc = column;
          let value = 0;
          while (nr >= 0 && nr < rows && nc >= 0 && nc < columns) {
            value = 10 * value + mat[nr][nc];
            if (value > 10) counts.set(value, (counts.get(value) || 0) + 1);
            nr += dr;
            nc += dc;
          }
        }
      }
    }
  }
  let best = -1;
  let frequency = 0;
  for (const [value, count] of counts) {
    if (count < frequency || (count === frequency && value <= best)) continue;
    if (value % 2 === 0) continue;
    let factor = 3;
    while (factor * factor <= value && value % factor !== 0) factor += 2;
    if (factor * factor > value) {
      best = value;
      frequency = count;
    }
  }
  return best;
}

const mostFrequentPrime = solve;
class Solution {
  mostFrequentPrime(mat) { return solve(mat); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostFrequentPrime };
