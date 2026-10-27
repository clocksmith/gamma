'use strict';

// 3946. Maximum Number of Items From Sale I.
// Specification: https://leetcode.com/problems/maximum-number-of-items-from-sale-i/description/
// O(n^2 + n * budget) time and O(budget) space. Inputs are preserved.
function solve(items, budget) {
  const best = new Array(budget + 1).fill(0);
  for (let index = 0; index < items.length; index++) {
    const [factor, price] = items[index];
    let bonus = 0;
    for (let other = 0; other < items.length; other++) {
      if (other !== index && items[other][0] % factor === 0) bonus++;
    }
    // Activate this type once, then add extra copies without repeating its bonus.
    for (let money = budget; money >= price; money--) {
      best[money] = Math.max(best[money], best[money - price] + 1 + bonus);
    }
    for (let money = price; money <= budget; money++) {
      best[money] = Math.max(best[money], best[money - price] + 1);
    }
  }
  return best[budget];
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
