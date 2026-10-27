'use strict';

// 3947. Maximum Number of Items From Sale II.
// Specification: https://leetcode.com/problems/maximum-number-of-items-from-sale-ii/description/
// O(n log n) time and O(n) space; buy cheapest bounded two-copy offers, then cheapest plain copies. Inputs are preserved.
function solve(items, budget) {
  const size = items.length;
  const frequency = new Int32Array(size + 1);
  let cheapest = Infinity;
  for (const [factor, price] of items) { frequency[factor]++; cheapest = Math.min(cheapest, price); }
  const targets = new Int32Array(size + 1);
  for (let factor = 1; factor <= size; factor++) {
    for (let multiple = factor; multiple <= size; multiple += factor) targets[factor] += frequency[multiple];
  }
  const offers = items.map(([factor, price]) => [price, targets[factor] - 1]).sort((a, b) => a[0] - b[0]);
  let money = budget;
  let answer = 0;
  for (const [price, available] of offers) {
    if (price >= 2 * cheapest) break;
    const copies = Math.min(available, Math.floor(money / price));
    answer += 2 * copies;
    money -= copies * price;
    if (copies < available) break;
  }
  return answer + Math.floor(money / cheapest);
}

if (typeof module !== 'undefined') module.exports = { solve };
