'use strict';

// 1833. Maximum Ice Cream Bars: count prices and buy affordable bars in ascending price order.
// O(n + M) time and O(M) auxiliary space, with M the largest price; inputs are read-only.
function solve(costs, coins) {
  let largest = 0;
  for (const cost of costs) largest = Math.max(largest, cost);
  const counts = new Int32Array(largest + 1);
  for (const cost of costs) counts[cost] += 1;
  let remaining = coins;
  let bought = 0;
  for (let price = 1; price <= largest && price <= remaining; price += 1) {
    const quantity = Math.min(counts[price], Math.floor(remaining / price));
    bought += quantity;
    remaining -= quantity * price;
  }
  return bought;
}

const maxIceCream = solve;
class Solution {
  maxIceCream(costs, coins) { return solve(costs, coins); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxIceCream };
