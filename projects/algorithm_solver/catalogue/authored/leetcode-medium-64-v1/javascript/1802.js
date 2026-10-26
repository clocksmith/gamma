'use strict';

// 1802. Maximum Value at a Given Index in a Bounded Array: binary search the peak using exact arithmetic-series costs for both sides.
// O(log(maxSum + 1)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(n, index, maxSum) {
  const leftLength = BigInt(index);
  const rightLength = BigInt(n - index - 1);
  const budget = BigInt(maxSum);
  function sideSum(length, height) {
    const descending = length < height - 1n ? length : height - 1n;
    return descending * (2n * height - descending - 1n) / 2n + length - descending;
  }
  let low = 1;
  let high = maxSum;
  while (low < high) {
    const middle = Math.floor((low + high + 1) / 2);
    const height = BigInt(middle);
    const needed = height + sideSum(leftLength, height) + sideSum(rightLength, height);
    if (needed <= budget) low = middle;
    else high = middle - 1;
  }
  return low;
}

const maxValue = solve;
class Solution {
  maxValue(n, index, maxSum) { return solve(n, index, maxSum); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxValue };
