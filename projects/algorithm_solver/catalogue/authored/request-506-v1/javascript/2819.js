// Original implementation. Contract: https://leetcode.com/problems/minimum-relative-loss-after-buying-chocolates/
"use strict";

function solve(prices, queries) {
  const sorted = [...prices].sort((a, b) => a - b);
  const n = sorted.length;
  const prefix = [0];
  for (const price of sorted) prefix.push(prefix.at(-1) + price);

  return queries.map(([k, count]) => {
    let left = 0;
    let right = n;
    while (left < right) {
      const middle = (left + right) >> 1;
      if (sorted[middle] <= k) left = middle + 1;
      else right = middle;
    }
    const cheapCount = left;
    let low = Math.max(0, count - (n - cheapCount));
    let high = Math.min(cheapCount, count);
    // Taking x cheapest items and count-x most expensive items is optimal
    // for fixed x. Its discrete derivative is nondecreasing.
    while (low < high) {
      const middle = (low + high) >> 1;
      if (sorted[middle] + sorted[n - count + middle] - 2 * k < 0) {
        low = middle + 1;
      } else {
        high = middle;
      }
    }
    const cheap = low;
    const expensive = count - cheap;
    return prefix[cheap] + 2 * k * expensive - (prefix[n] - prefix[n - expensive]);
  });
}

module.exports = solve;
