/* Original candidate for LeetCode 2117. Contract: https://leetcode.com/problems/abbreviating-the-product-of-a-range/
Development tests only; not admitted or independently qualified.
Positional arguments match the official function; inputs are not mutated.
Complexity: Exact arbitrary-precision product; O((right-left+1)*B) bit-arithmetic upper bound, O(B) bits; B=product bit length */
"use strict";

function solve(left, right) {
  let product = 1n;
  for (let value = left; value <= right; value++) {
    product *= BigInt(value);
  }
  let trailingZeros = 0;
  while (product % 10n === 0n) {
    product /= 10n;
    trailingZeros++;
  }
  const digits = product.toString();
  const abbreviation = digits.length <= 10
    ? digits
    : digits.slice(0, 5) + '...' + digits.slice(-5);
  return abbreviation + 'e' + trailingZeros;
}

module.exports = solve;
