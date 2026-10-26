'use strict';

// 2861. Maximum Number of Alloys: binary search each machine using its exact metal shortfall cost.
// O(k * n * log(U + 1)) time and O(1) auxiliary space, where U is the per-machine production bound; inputs are read-only.
function solve(n, k, budget, composition, stock, cost) {
  let best = 0;
  for (let machine = 0; machine < k; machine += 1) {
    const recipe = composition[machine];
    let upper = Infinity;
    for (let index = 0; index < n; index += 1) {
      upper = Math.min(upper, Math.floor((stock[index] + Math.floor(budget / cost[index])) / recipe[index]));
    }
    let low = 0;
    let high = upper;
    while (low < high) {
      const amount = Math.floor((low + high + 1) / 2);
      let spending = 0;
      for (let index = 0; index < n; index += 1) {
        spending += Math.max(0, amount * recipe[index] - stock[index]) * cost[index];
        if (spending > budget) break;
      }
      if (spending <= budget) low = amount;
      else high = amount - 1;
    }
    best = Math.max(best, low);
  }
  return best;
}

const maxNumberOfAlloys = solve;
class Solution {
  maxNumberOfAlloys(n, k, budget, composition, stock, cost) { return solve(n, k, budget, composition, stock, cost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxNumberOfAlloys };
