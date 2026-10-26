'use strict';

// 3768. Minimum Inversion Count in Subarrays of Fixed Length.
// O(n log n) time and O(n) space; sliding Fenwick counts exclude equal values from inversions.
function solve(nums, k) {
  const values = [...new Set(nums)].sort((left, right) => left - right);
  const rank = new Map(values.map((value, index) => [value, index + 1]));
  const tree = new Int32Array(values.length + 1);
  function update(index, delta) {
    while (index < tree.length) {
      tree[index] += delta;
      index += index & -index;
    }
  }
  function prefix(index) {
    let total = 0;
    while (index > 0) {
      total += tree[index];
      index -= index & -index;
    }
    return total;
  }
  let inversions = 0;
  let answer = Infinity;
  let size = 0;
  for (let index = 0; index < nums.length; index += 1) {
    if (index >= k) {
      const old = rank.get(nums[index - k]);
      inversions -= prefix(old - 1);
      update(old, -1);
      size -= 1;
    }
    const position = rank.get(nums[index]);
    inversions += size - prefix(position);
    update(position, 1);
    size += 1;
    if (size === k) answer = Math.min(answer, inversions);
  }
  return answer;
}

const minInversionCount = solve;
class Solution {
  minInversionCount(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minInversionCount };
