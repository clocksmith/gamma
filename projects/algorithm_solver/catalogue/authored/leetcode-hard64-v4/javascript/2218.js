'use strict';

// 2218. Maximum Value of K Coins From Piles. Multiple-choice knapsack over pile prefixes; O(k*sum(min(k,len(pile)))) time, O(k) auxiliary space. Inputs are preserved.

function solve(piles, k) {
  let best = Array(k + 1).fill(-Infinity);
  best[0] = 0;
  for (const pile of piles) {
    const prefix = [0];
    for (let index = 0; index < Math.min(k, pile.length); index += 1) {
      prefix.push(prefix[prefix.length - 1] + pile[index]);
    }
    const following = best.slice();
    for (let used = 0; used <= k; used += 1) {
      if (best[used] === -Infinity) continue;
      const maximum = Math.min(prefix.length - 1, k - used);
      for (let count = 1; count <= maximum; count += 1) {
        following[used + count] = Math.max(following[used + count], best[used] + prefix[count]);
      }
    }
    best = following;
  }
  return best[k];
}

const maxValueOfCoins = solve;
class Solution {
  maxValueOfCoins(piles, k) { return solve(piles, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxValueOfCoins };
