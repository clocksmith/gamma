'use strict';

// 1851. Minimum Interval to Include Each Query. Offline query sweep with a minimum-length heap; O((n+q) log(n+q)) time and O(n+q) space. Inputs are preserved.

class MinHeap {
  constructor(less) {
    this.items = [];
    this.less = less;
  }
  get size() { return this.items.length; }
  peek() { return this.items[0]; }
  push(value) {
    const items = this.items;
    let index = items.length;
    items.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.less(value, items[parent])) break;
      items[index] = items[parent];
      index = parent;
    }
    items[index] = value;
  }
  pop() {
    const items = this.items;
    const first = items[0];
    const last = items.pop();
    if (items.length > 0) {
      let index = 0;
      while (index * 2 + 1 < items.length) {
        let child = index * 2 + 1;
        if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
        if (!this.less(items[child], last)) break;
        items[index] = items[child];
        index = child;
      }
      items[index] = last;
    }
    return first;
  }
}

function solve(intervals, queries) {
  const ordered = intervals.slice().sort((a, b) => a[0] - b[0]);
  const pending = queries.map((value, index) => [value, index]).sort((a, b) => a[0] - b[0]);
  const answer = Array(queries.length).fill(-1);
  const available = new MinHeap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]));
  let cursor = 0;
  for (const [query, index] of pending) {
    while (cursor < ordered.length && ordered[cursor][0] <= query) {
      const [left, right] = ordered[cursor];
      available.push([right - left + 1, right]);
      cursor += 1;
    }
    while (available.size > 0 && available.peek()[1] < query) available.pop();
    if (available.size > 0) answer[index] = available.peek()[0];
  }
  return answer;
}

const minInterval = solve;
class Solution {
  minInterval(intervals, queries) { return solve(intervals, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minInterval };
