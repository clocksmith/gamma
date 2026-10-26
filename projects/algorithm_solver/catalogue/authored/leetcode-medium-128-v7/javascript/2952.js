'use strict';

// 2952. Minimum Number of Coins to be Added: extend the covered prefix of sums and add its first missing value when necessary.
// O(n log n + log(target + 1)) time and O(n) auxiliary space; inputs are read-only.
function solve(coins, target) {
  const ordered = coins.slice().sort((left, right) => left - right);
  let missing = 1;
  let index = 0;
  let added = 0;
  while (missing <= target) {
    if (index < ordered.length && ordered[index] <= missing) {
      missing += ordered[index];
      index += 1;
    } else {
      missing *= 2;
      added += 1;
    }
  }
  return added;
}

const minimumAddedCoins = solve;
class Solution {
  minimumAddedCoins(coins, target) { return solve(coins, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumAddedCoins };
