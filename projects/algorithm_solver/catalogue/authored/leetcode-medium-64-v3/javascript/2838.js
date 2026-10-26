'use strict';

// 2838. Maximum Coins Heroes Can Collect: sort monsters by power and query cumulative rewards.
// O(m log m + h log(m + 1)) time and O(m + h) space for m monsters and h heroes; inputs are read-only.
function solve(heroes, monsters, coins) {
  const ordered = monsters.map((power, index) => [power, coins[index]]);
  ordered.sort((left, right) => left[0] - right[0]);
  const rewards = [0];
  for (const monster of ordered) rewards.push(rewards[rewards.length - 1] + monster[1]);
  return heroes.map(hero => {
    let left = 0;
    let right = ordered.length;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (ordered[middle][0] <= hero) left = middle + 1;
      else right = middle;
    }
    return rewards[left];
  });
}

const maximumCoins = solve;
class Solution {
  maximumCoins(heroes, monsters, coins) { return solve(heroes, monsters, coins); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumCoins };
