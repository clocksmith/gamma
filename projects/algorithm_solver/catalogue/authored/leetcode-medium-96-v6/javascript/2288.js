'use strict';

// 2288. Apply Discount to Prices: recognize whole price tokens and format the discount using integer cents.
// O(L) time and O(L) auxiliary and result space on the bounded price domain; inputs are read-only.
function solve(sentence, discount) {
  const factor = BigInt(100 - discount);
  return sentence.split(' ').map(token => {
    if (!/^[$][0-9]+$/.test(token)) return token;
    const cents = BigInt(token.slice(1)) * factor;
    return '$' + (cents / 100n).toString() + '.' + (cents % 100n).toString().padStart(2, '0');
  }).join(' ');
}

const discountPrices = solve;
class Solution {
  discountPrices(sentence, discount) { return solve(sentence, discount); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, discountPrices };
