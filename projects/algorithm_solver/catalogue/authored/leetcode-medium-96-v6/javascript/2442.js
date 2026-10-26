'use strict';

// 2442. Count Number of Distinct Integers After Reverse Operations: collect every original integer and its reversed decimal value.
// O(n d) expected time and O(n) auxiliary space for at most d decimal digits; inputs are read-only.
function solve(nums) {
  const values = new Set(nums);
  for (const value of nums) {
    let remaining = value;
    let reversedValue = 0;
    while (remaining > 0) {
      reversedValue = reversedValue * 10 + remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    values.add(reversedValue);
  }
  return values.size;
}

const countDistinctIntegers = solve;
class Solution {
  countDistinctIntegers(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countDistinctIntegers };
