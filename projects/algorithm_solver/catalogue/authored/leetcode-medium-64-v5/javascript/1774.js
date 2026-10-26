'use strict';

// 1774. Closest Dessert Cost: enumerate distinct topping totals and compare every base with explicit lower-cost tie breaking.
// O((b + 1) * 3^t) expected time and O(3^t) space, with b bases and t toppings; inputs are read-only.
function solve(baseCosts, toppingCosts, target) {
  let totals = new Set([0]);
  for (const cost of toppingCosts) {
    const next = new Set();
    for (const total of totals) {
      next.add(total);
      next.add(total + cost);
      next.add(total + 2 * cost);
    }
    totals = next;
  }
  let best = baseCosts[0];
  for (const base of baseCosts) {
    for (const topping of totals) {
      const candidate = base + topping;
      const difference = Math.abs(candidate - target);
      if (difference < Math.abs(best - target) ||
          (difference === Math.abs(best - target) && candidate < best)) best = candidate;
    }
  }
  return best;
}

const closestCost = solve;
class Solution {
  closestCost(baseCosts, toppingCosts, target) { return solve(baseCosts, toppingCosts, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, closestCost };
