'use strict';

// 1439. Find the Kth Smallest Sum of a Matrix With Sorted Rows: merge only the k smallest partial sums; O(rows*k*log(k+1)) time and O(k) space.

class _MinHeap {
  constructor(compare = (a, b) => a - b) {
    this.items = [];
    this.compare = compare;
  }

  get size() { return this.items.length; }
  peek() { return this.items[0]; }

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
    if (items.length === 0) return undefined;
    const result = items[0];
    const last = items.pop();
    if (items.length > 0) {
      let index = 0;
      while (index * 2 + 1 < items.length) {
        let child = index * 2 + 1;
        if (child + 1 < items.length &&
            this.compare(items[child + 1], items[child]) < 0) child += 1;
        if (this.compare(last, items[child]) <= 0) break;
        items[index] = items[child];
        index = child;
      }
      items[index] = last;
    }
    return result;
  }
}

function solve(mat, k) {
  let partial = [0];
  for (const row of mat) {
    const heap = new _MinHeap((a, b) => a[0] - b[0]);
    for (let index = 0; index < partial.length; index += 1) heap.push([partial[index] + row[0], index, 0]);
    const following = [];
    while (heap.size > 0 && following.length < k) {
      const [value, previousIndex, column] = heap.pop();
      following.push(value);
      if (column + 1 < row.length) heap.push([partial[previousIndex] + row[column + 1], previousIndex, column + 1]);
    }
    partial = following;
  }
  return partial[k - 1];
}

const kthSmallest = solve;
class Solution {
  kthSmallest(mat, k) { return solve(mat, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthSmallest };
