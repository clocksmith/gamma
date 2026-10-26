'use strict';

// 3505. Minimum Operations to Make Elements Within K Subarrays Equal.
// Fenwick order statistics give sliding median costs; a second dynamic program selects disjoint windows; O(n log n+n*k) time and O(n) space. Inputs are preserved.

function solve(nums, x, k) {
  const values = [...new Set(nums)].sort((a, b) => a - b), size = values.length;
  const rank = new Map(values.map((value, index) => [value, index + 1]));
  const counts = new Int32Array(size + 1), sums = new Float64Array(size + 1);
  function change(value, difference) {
    for (let index = rank.get(value); index <= size; index += index & -index) {
      counts[index] += difference; sums[index] += difference * value;
    }
  }
  let firstStep = 1;
  while (firstStep * 2 <= size) firstStep *= 2;
  function medianPrefix(amount) {
    let index = 0, count = 0, total = 0;
    for (let step = firstStep; step > 0; step = Math.floor(step / 2)) {
      const following = index + step;
      if (following <= size && count + counts[following] < amount) {
        index = following; count += counts[following]; total += sums[following];
      }
    }
    return [values[index], count, total];
  }
  const windowCost = new Float64Array(nums.length - x + 1);
  let total = 0;
  for (let index = 0; index < nums.length; index += 1) {
    change(nums[index], 1); total += nums[index];
    if (index >= x) { change(nums[index - x], -1); total -= nums[index - x]; }
    if (index + 1 >= x) {
      const [median, below, belowSum] = medianPrefix(Math.ceil(x / 2));
      windowCost[index - x + 1] = median * below - belowSum + total - belowSum - median * (x - below);
    }
  }
  let previous = new Float64Array(nums.length + 1);
  for (let selected = 1; selected <= k; selected += 1) {
    const current = new Float64Array(nums.length + 1).fill(Infinity);
    for (let end = selected * x; end <= nums.length; end += 1) current[end] = Math.min(current[end - 1], previous[end - x] + windowCost[end - x]);
    previous = current;
  }
  return previous[nums.length];
}

const minOperations = solve;
class Solution {
  minOperations(nums, x, k) { return solve(nums, x, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
