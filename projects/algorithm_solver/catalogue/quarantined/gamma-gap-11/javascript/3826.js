'use strict';

// 3826. Minimum Partition Score.
// O(k n log n) time and O(n) space; convex positive-prefix costs give monotone optimal split positions.
function solve(nums, k) {
  const n = nums.length;
  const prefix = [0];
  for (const value of nums) prefix.push(prefix[prefix.length - 1] + value);
  let previous = Array(n + 1).fill(Infinity);
  previous[0] = 0;
  for (let groups = 1; groups <= k; groups += 1) {
    const current = Array(n + 1).fill(Infinity);
    function compute(left, right, first, last) {
      if (left > right) return;
      const middle = Math.floor((left + right) / 2);
      let best = Infinity;
      let split = first;
      for (let index = first; index <= Math.min(last, middle - 1); index += 1) {
        const total = prefix[middle] - prefix[index];
        const value = previous[index] + total * (total + 1) / 2;
        if (value < best) {
          best = value;
          split = index;
        }
      }
      current[middle] = best;
      compute(left, middle - 1, first, split);
      compute(middle + 1, right, split, last);
    }
    compute(groups, n, groups - 1, n - 1);
    previous = current;
  }
  return previous[n];
}

const minPartitionScore = solve;
class Solution {
  minPartitionScore(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minPartitionScore };
