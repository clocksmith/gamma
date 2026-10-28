'use strict';

// 638. Shopping Offers (Medium).
// Specification: https://leetcode.com/problems/shopping-offers/description/
function solve(price, special, needs) {
  const memo = new Map();
  function dfs(current) {
    const key = current.join(',');
    if (memo.has(key)) return memo.get(key);
    let best = 0;
    for (let i = 0; i < current.length; i++) best += current[i] * price[i];
    for (const offer of special) {
      const next = current.slice();
      let valid = true;
      for (let i = 0; i < current.length; i++) {
        next[i] -= offer[i];
        if (next[i] < 0) { valid = false; break; }
      }
      if (valid) best = Math.min(best, offer[offer.length - 1] + dfs(next));
    }
    memo.set(key, best);
    return best;
  }
  return dfs(needs.slice());
}
const shoppingOffers = solve;
class Solution { shoppingOffers(price, special, needs) { return solve(price, special, needs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, shoppingOffers };
