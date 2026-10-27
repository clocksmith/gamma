'use strict';

// 638. Shopping Offers.

function solve(price, special, needs) {
  const size = price.length;
  const offers = special.filter(offer => offer.slice(0, size).some(value => value > 0)
    && offer.slice(0, size).every((value, i) => value <= needs[i])
    && offer[size] < offer.slice(0, size).reduce((sum, value, i) => sum + value * price[i], 0));
  const memo = new Map();
  function cost(remaining) {
    const key = remaining.join(',');
    if (memo.has(key)) return memo.get(key);
    let best = remaining.reduce((sum, value, i) => sum + value * price[i], 0);
    for (const offer of offers) {
      if (remaining.every((value, i) => offer[i] <= value)) {
        best = Math.min(best, offer[size] + cost(remaining.map((value, i) => value - offer[i])));
      }
    }
    memo.set(key, best); return best;
  }
  return cost(needs.slice());
}

const shoppingOffers = solve;
class Solution {
  shoppingOffers(price, special, needs) { return solve(price, special, needs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, shoppingOffers };
