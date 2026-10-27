/**
 * 4014. Minimum Total Price After Applying Discounts
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-total-price-after-applying-discounts/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4014.Minimum%20Total%20Price%20After%20Applying%20Discounts/README_EN.md
 * Complexity: O(n log n + m log m) time, O(n+m) space.
 * Match largest discounts to largest prices. Accumulate exact integer hundredths; perform one final division without per-item rounding. Inputs preserved.
 */

function solve(prices, discounts) {
  const ordered = prices.slice().sort((a, b) => b - a), offers = discounts.slice().sort((a, b) => b - a);
  let hundredths = 0;
  for (const price of ordered) hundredths += price * 100;
  for (let i = 0; i < Math.min(ordered.length, offers.length); i++) hundredths -= ordered[i] * offers[i];
  return hundredths / 100;
}

function minPrice(prices, discounts) {
  return solve(prices, discounts);
}

class Solution {
  minPrice(prices, discounts) {
    return solve(prices, discounts);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, minPrice, Solution };
}
