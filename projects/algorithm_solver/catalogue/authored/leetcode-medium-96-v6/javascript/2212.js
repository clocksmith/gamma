'use strict';

// 2212. Maximum Points in an Archery Competition: enumerate winning scoring regions and place unused arrows in region zero.
// O(b * 2^b) time and O(b) space for the fixed b = 11 scoring regions; inputs are read-only.
function solve(numArrows, aliceArrows) {
  let bestScore = -1;
  let bestMask = 0;
  for (let mask = 0; mask < (1 << 11); mask += 1) {
    let used = 0;
    let score = 0;
    for (let region = 1; region < 12; region += 1) {
      if (mask & (1 << (region - 1))) {
        used += aliceArrows[region] + 1;
        score += region;
      }
    }
    if (used <= numArrows && score > bestScore) {
      bestScore = score;
      bestMask = mask;
    }
  }
  const result = new Array(12).fill(0);
  let remaining = numArrows;
  for (let region = 1; region < 12; region += 1) {
    if (bestMask & (1 << (region - 1))) {
      result[region] = aliceArrows[region] + 1;
      remaining -= result[region];
    }
  }
  result[0] = remaining;
  return result;
}

const maximumBobPoints = solve;
class Solution {
  maximumBobPoints(numArrows, aliceArrows) { return solve(numArrows, aliceArrows); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumBobPoints };
