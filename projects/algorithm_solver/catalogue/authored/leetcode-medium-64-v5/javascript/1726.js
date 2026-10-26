'use strict';

// 1726. Tuple with Same Product: count earlier unordered pairs with the same product.
// O(n^2) expected time and O(n^2) auxiliary space; inputs are read-only.
function solve(nums) {
  const counts = new Map();
  let result = 0;
  for (let right = 0; right < nums.length; right += 1) {
    for (let left = 0; left < right; left += 1) {
      const product = nums[left] * nums[right];
      const previous = counts.get(product) || 0;
      result += 8 * previous;
      counts.set(product, previous + 1);
    }
  }
  return result;
}

const tupleSameProduct = solve;
class Solution {
  tupleSameProduct(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, tupleSameProduct };
