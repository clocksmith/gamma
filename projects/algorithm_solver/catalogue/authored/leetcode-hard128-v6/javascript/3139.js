'use strict';

// 3139. Minimum Cost to Equalize Array.
// Evaluate the boundary between unbalanced deficits and pairable deficits, including parity neighbors; O(n) time, O(1) space. Exact integer costs precede modulo.

function solve(nums, cost1, cost2) {
  let total = 0, minimum = Infinity, maximum = -Infinity;
  for (const value of nums) { total += value; minimum = Math.min(minimum, value); maximum = Math.max(maximum, value); }
  const n = nums.length, c1 = BigInt(cost1), c2 = BigInt(cost2), count = BigInt(n), sum = BigInt(total), mod = 1000000007n;
  let answer = (count * BigInt(maximum) - sum) * c1;
  if (n <= 2 || cost2 >= 2 * cost1) return Number(answer % mod);
  const boundary = Math.max(maximum, Math.ceil((total - 2 * minimum) / (n - 2)));
  for (const target of new Set([maximum, maximum + 1, boundary - 1, boundary, boundary + 1])) {
    if (target < maximum) continue;
    const deficit = count * BigInt(target) - sum, largest = BigInt(target - minimum);
    const pairs = deficit / 2n < deficit - largest ? deficit / 2n : deficit - largest;
    const price = pairs * c2 + (deficit - 2n * pairs) * c1;
    if (price < answer) answer = price;
  }
  return Number(answer % mod);
}

const minCostToEqualizeArray = solve;
class Solution {
  minCostToEqualizeArray(nums, cost1, cost2) { return solve(nums, cost1, cost2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCostToEqualizeArray };
