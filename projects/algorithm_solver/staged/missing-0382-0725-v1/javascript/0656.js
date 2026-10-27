'use strict';

// 656. Coin Path. Suffix minimum costs choose the smallest next index on ties.

function solve(coins, maxJump) {
  const n = coins.length;
  if (n === 0 || coins[0] === -1 || coins[n - 1] === -1) return [];
  const cost = Array(n).fill(Infinity), next = Array(n).fill(-1);
  cost[n - 1] = coins[n - 1];
  for (let i = n - 2; i >= 0; i -= 1) {
    if (coins[i] === -1) continue;
    for (let j = i + 1; j < Math.min(n, i + maxJump + 1); j += 1) {
      const candidate = coins[i] + cost[j];
      if (candidate < cost[i]) { cost[i] = candidate; next[i] = j; }
    }
  }
  if (!Number.isFinite(cost[0])) return [];
  const answer = [];
  for (let index = 0; index !== -1; index = next[index]) answer.push(index + 1);
  return answer;
}

const cheapestJump = solve;
class Solution {
  cheapestJump(coins, maxJump) { return solve(coins, maxJump); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, cheapestJump };
