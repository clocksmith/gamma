'use strict';

// 2749. Minimum Operations to Make the Integer Zero: find the first operation count whose remaining value is a sum of that many powers of two.
// O(60 * 60) bounded bit operations and O(1) auxiliary space on the stated domain; inputs are read-only.
function solve(num1, num2) {
  const first = BigInt(num1);
  const second = BigInt(num2);
  for (let operations = 1; operations <= 60; operations += 1) {
    const remaining = first - BigInt(operations) * second;
    if (remaining < BigInt(operations)) continue;
    let bits = remaining;
    let count = 0;
    while (bits !== 0n) {
      bits &= bits - 1n;
      count += 1;
    }
    if (count <= operations) return operations;
  }
  return -1;
}

const makeTheIntegerZero = solve;
class Solution {
  makeTheIntegerZero(num1, num2) { return solve(num1, num2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeTheIntegerZero };
