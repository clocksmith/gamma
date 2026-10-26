'use strict';

// 2226. Maximum Candies Allocated to K Children: binary search the largest equal portion supported by splitting the piles.
// O(n log M) time and O(1) auxiliary space for maximum pile M; inputs are read-only.
function solve(candies, k) {
  let low = 0;
  let high = 0;
  for (const pile of candies) high = Math.max(high, pile);
  while (low < high) {
    const middle = Math.floor((low + high + 1) / 2);
    let portions = 0;
    for (const pile of candies) {
      portions += Math.floor(pile / middle);
      if (portions >= k) break;
    }
    if (portions >= k) low = middle;
    else high = middle - 1;
  }
  return low;
}

const maximumCandies = solve;
class Solution {
  maximumCandies(candies, k) { return solve(candies, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumCandies };
