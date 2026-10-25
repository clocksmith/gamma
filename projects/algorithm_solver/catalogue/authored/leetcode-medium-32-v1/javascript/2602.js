'use strict';

// 2602. Minimum Operations to Make All Array Elements Equal: answer absolute-distance sums with sorted prefixes.
// O(n log n + q log n) time and O(n) auxiliary space excluding the result; inputs are read-only.
function solve(nums, queries) {
  const values = [...nums].sort((left, right) => left - right);
  const prefix = [0];
  for (const value of values) prefix.push(prefix[prefix.length - 1] + value);
  const answer = [];
  for (const query of queries) {
    let low = 0;
    let high = values.length;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (values[middle] < query) low = middle + 1;
      else high = middle;
    }
    const split = low;
    const leftCost = query * split - prefix[split];
    const rightCost = prefix[values.length] - prefix[split] - query * (values.length - split);
    answer.push(leftCost + rightCost);
  }
  return answer;
}

const minOperations = solve;
class Solution {
  minOperations(nums, queries) { return solve(nums, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
