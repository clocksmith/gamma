'use strict';

// 2070. Most Beautiful Item for Each Query: index prefix-maximum beauty by sorted price and binary search each budget.
// O(n log n + q log n) time and O(n + q) auxiliary and result space; inputs are read-only.
function solve(items, queries) {
  const ordered = items.slice().sort((left, right) => left[0] - right[0]);
  const prices = [];
  const beauty = [];
  let best = 0;
  for (const [price, value] of ordered) {
    prices.push(price);
    best = Math.max(best, value);
    beauty.push(best);
  }
  return queries.map(query => {
    let low = 0;
    let high = prices.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (prices[middle] <= query) low = middle + 1;
      else high = middle;
    }
    return low > 0 ? beauty[low - 1] : 0;
  });
}

const maximumBeauty = solve;
class Solution {
  maximumBeauty(items, queries) { return solve(items, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumBeauty };
