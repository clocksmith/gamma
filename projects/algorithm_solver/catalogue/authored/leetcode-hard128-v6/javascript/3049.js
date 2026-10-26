'use strict';

// 3049. Earliest Second to Mark Indices II.
// Binary search with reverse-time greedy selection of resets and reserved later marks; O(m log n log m) time, O(n+m) space. Inputs are preserved.

class MinHeap {
  constructor(compare = (a, b) => a - b) {
    this.items = [];
    this.compare = compare;
  }
  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (this.compare(items[parent], value) <= 0) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }
  pop() {
    const items = this.items;
    const answer = items[0];
    const last = items.pop();
    if (items.length === 0) return answer;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.compare(items[child + 1], items[child]) < 0) child += 1;
      if (this.compare(last, items[child]) <= 0) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = last;
    return answer;
  }
}

function solve(nums, changeIndices) {
  const n = nums.length, m = changeIndices.length, first = Array(n).fill(m);
  changeIndices.forEach((value, second) => { first[value - 1] = Math.min(first[value - 1], second); });
  const baseline = nums.reduce((sum, value) => sum + value, n);
  function possible(limit) {
    let free = 0, saved = 0;
    const selected = new MinHeap();
    for (let second = limit - 1; second >= 0; second -= 1) {
      const index = changeIndices[second] - 1;
      if (first[index] !== second || nums[index] <= 1) { free += 1; continue; }
      selected.push(nums[index]); saved += nums[index] + 1; free -= 1;
      if (free < 0) { saved -= selected.pop() + 1; free += 2; }
    }
    return free >= baseline - saved;
  }
  if (n > m || !possible(m)) return -1;
  let low = n, high = m;
  while (low < high) {
    const middle = Math.floor((low + high) / 2);
    if (possible(middle)) high = middle; else low = middle + 1;
  }
  return low;
}

const earliestSecondToMarkIndices = solve;
class Solution {
  earliestSecondToMarkIndices(nums, changeIndices) { return solve(nums, changeIndices); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, earliestSecondToMarkIndices };
