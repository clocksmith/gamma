'use strict';

// 1423. Maximum Points You Can Obtain from Cards: exchange cards from the left prefix for the right suffix.
// O(k) time and O(1) auxiliary space; inputs are read-only.
function solve(cardPoints, k) {
  let total = 0;
  for (let index = 0; index < k; index += 1) total += cardPoints[index];
  let best = total;
  for (let takenRight = 1; takenRight <= k; takenRight += 1) {
    total += cardPoints[cardPoints.length - takenRight] - cardPoints[k - takenRight];
    best = Math.max(best, total);
  }
  return best;
}

const maxScore = solve;
class Solution {
  maxScore(cardPoints, k) { return solve(cardPoints, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxScore };
