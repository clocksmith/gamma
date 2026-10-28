'use strict';

// 1268. Search Suggestions System (Medium).
// Specification: https://leetcode.com/problems/search-suggestions-system/description/
function solve(products, searchWord) {
  const sorted = products.slice().sort();
  const result = [];
  for (let length = 1; length <= searchWord.length; length++) {
    const prefix = searchWord.slice(0, length);
    const matches = [];
    for (const product of sorted) { if (product.startsWith(prefix)) { matches.push(product); if (matches.length === 3) break; } }
    result.push(matches);
  }
  return result;
}
const suggestedProducts = solve;
class Solution { suggestedProducts(products, searchWord) { return solve(products, searchWord); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, suggestedProducts };
