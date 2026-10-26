'use strict';

// 2343. Query Kth Smallest Trimmed Number: answer queries during stable least-significant-digit sorting.
// O((n + 10) T + q) time and O(n + q + T) space for maximum requested trim T; inputs are read-only.
function solve(nums, queries) {
  let maximumTrim = 0;
  for (const [, trim] of queries) maximumTrim = Math.max(maximumTrim, trim);
  const byTrim = Array.from({ length: maximumTrim + 1 }, () => []);
  for (let index = 0; index < queries.length; index += 1) {
    const [rank, trim] = queries[index];
    byTrim[trim].push([rank, index]);
  }
  let order = Array.from({ length: nums.length }, (_, index) => index);
  const result = new Array(queries.length).fill(0);
  const width = nums[0].length;
  for (let trim = 1; trim <= maximumTrim; trim += 1) {
    const buckets = Array.from({ length: 10 }, () => []);
    const column = width - trim;
    for (const index of order) buckets[nums[index].charCodeAt(column) - 48].push(index);
    order = [];
    for (const bucket of buckets) for (const index of bucket) order.push(index);
    for (const [rank, queryIndex] of byTrim[trim]) result[queryIndex] = order[rank - 1];
  }
  return result;
}

const smallestTrimmedNumbers = solve;
class Solution {
  smallestTrimmedNumbers(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestTrimmedNumbers };
