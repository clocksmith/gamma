'use strict';

// O(n log(max(piles))) time, O(1) auxiliary space. Sums use Number, not int32.
function solve(piles, h) {
  let low = 1;
  let high = 1;
  for (const pile of piles) high = Math.max(high, pile);
  while (low < high) {
    const speed = low + Math.floor((high - low) / 2);
    let hours = 0;
    for (const pile of piles) {
      hours += Math.floor((pile + speed - 1) / speed);
      if (hours > h) break;
    }
    if (hours <= h) high = speed;
    else low = speed + 1;
  }
  return low;
}

const minEatingSpeed = solve;
class Solution {
  minEatingSpeed(piles, h) { return solve(piles, h); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minEatingSpeed };
