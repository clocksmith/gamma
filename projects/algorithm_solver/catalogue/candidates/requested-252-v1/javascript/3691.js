/**
 * 3691. Maximum Total Subarray Value II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-total-subarray-value-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3691.Maximum%20Total%20Subarray%20Value%20II/README_EN.md
 * Complexity: O((n+k) log n) time; O(n log n) space.
 * Inputs preserved. Distinct (left,right) subarrays; sum <= 1e14 is exact as a JavaScript Number.
 */

class BinaryHeap {
  constructor(less) { this.items = []; this.less = less; }
  get length() { return this.items.length; }
  peek() { return this.items[0]; }
  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[index] = items[parent]; index = parent;
    }
    items[index] = value;
  }
  pop() {
    const items = this.items, result = items[0], last = items.pop();
    if (items.length === 0) return result;
    let index = 0;
    while (index * 2 + 1 < items.length) {
      let child = index * 2 + 1;
      if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
      if (!this.less(items[child], last)) break;
      items[index] = items[child]; index = child;
    }
    items[index] = last;
    return result;
  }
}

function solve(nums, k) {
  const n = nums.length, maximum = [nums.slice()], minimum = [nums.slice()];
  for (let width = 1; 2 * width <= n; width *= 2) {
    const previousMax = maximum[maximum.length - 1], previousMin = minimum[minimum.length - 1];
    const high = [], low = [];
    for (let i = 0; i + 2 * width <= n; i += 1) {
      high.push(Math.max(previousMax[i], previousMax[i + width]));
      low.push(Math.min(previousMin[i], previousMin[i + width]));
    }
    maximum.push(high); minimum.push(low);
  }
  const logs = Array(n + 1).fill(0);
  for (let i = 2; i <= n; i += 1) logs[i] = logs[Math.floor(i / 2)] + 1;
  function value(left, right) {
    const power = logs[right - left + 1], offset = right - 2 ** power + 1;
    return Math.max(maximum[power][left], maximum[power][offset]) - Math.min(minimum[power][left], minimum[power][offset]);
  }
  const heap = new BinaryHeap((a, b) => a[0] > b[0]);
  for (let left = 0; left < n; left += 1) heap.push([value(left, n - 1), left, n - 1]);
  let answer = 0;
  for (let chosen = 0; chosen < k; chosen += 1) {
    const [score, left, right] = heap.pop(); answer += score;
    if (right > left) heap.push([value(left, right - 1), left, right - 1]);
  }
  return answer;
}

function maxTotalValue(nums, k) {
  return solve(nums, k);
}

class Solution {
  maxTotalValue(nums, k) {
    return solve(nums, k);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxTotalValue, Solution };
}
