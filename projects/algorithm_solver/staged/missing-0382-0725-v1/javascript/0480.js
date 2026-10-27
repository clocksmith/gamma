'use strict';

// 480. Sliding Window Median. Coordinate-compressed frequency tree; O(n log n) time and O(n) space.

class _Fenwick {
  constructor(n) { this.tree = Array(n + 1).fill(0); }
  add(i, delta) {
    while (i < this.tree.length) { this.tree[i] += delta; i += i & -i; }
  }
  prefix(i) {
    let total = 0;
    while (i > 0) { total += this.tree[i]; i -= i & -i; }
    return total;
  }
}

function solve(nums, k) {
  const values = Array.from(new Set(nums)).sort((a, b) => a - b);
  const ranks = new Map(values.map((value, i) => [value, i + 1])), tree = new _Fenwick(values.length);
  function select(order) {
    let index = 0, step = 1;
    while (step * 2 <= values.length) step *= 2;
    while (step > 0) {
      const candidate = index + step;
      if (candidate < tree.tree.length && tree.tree[candidate] < order) {
        index = candidate; order -= tree.tree[candidate];
      }
      step = Math.floor(step / 2);
    }
    return values[index];
  }
  const answer = [];
  for (let i = 0; i < nums.length; i += 1) {
    tree.add(ranks.get(nums[i]), 1);
    if (i >= k) tree.add(ranks.get(nums[i - k]), -1);
    if (i + 1 >= k) {
      answer.push(k % 2 ? select(Math.floor(k / 2) + 1) : (select(k / 2) + select(k / 2 + 1)) / 2);
    }
  }
  return answer;
}

const medianSlidingWindow = solve;
class Solution {
  medianSlidingWindow(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, medianSlidingWindow };
