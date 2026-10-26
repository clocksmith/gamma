'use strict';

// 1792. Maximum Average Pass Ratio: assign each extra student to the largest exact marginal gain.
// O((n + e) * log(n + 1)) time and O(n) space, with e extra students; inputs are read-only.
class MinHeap {
  constructor(before) {
    this.values = [];
    this.before = before;
  }

  get size() { return this.values.length; }

  peek() { return this.values[0]; }

  push(value) {
    const values = this.values;
    let index = values.length;
    values.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (!this.before(value, values[parent])) break;
      values[index] = values[parent];
      index = parent;
    }
    values[index] = value;
  }

  pop() {
    const values = this.values;
    const result = values[0];
    const last = values.pop();
    if (values.length === 0) return result;
    let index = 0;
    while (2 * index + 1 < values.length) {
      let child = 2 * index + 1;
      if (child + 1 < values.length && this.before(values[child + 1], values[child])) child += 1;
      if (!this.before(values[child], last)) break;
      values[index] = values[child];
      index = child;
    }
    values[index] = last;
    return result;
  }
}

function solve(classes, extraStudents) {
  const heap = new MinHeap((a, b) => {
    // Each cross product is below 2^53 under the problem's bounds.
    const left = (a[1] - a[0]) * b[1] * (b[1] + 1);
    const right = (b[1] - b[0]) * a[1] * (a[1] + 1);
    return left > right || (left === right && a[2] < b[2]);
  });
  for (let index = 0; index < classes.length; index += 1) {
    heap.push([classes[index][0], classes[index][1], index]);
  }
  for (let count = 0; count < extraStudents; count += 1) {
    const current = heap.pop();
    current[0] += 1;
    current[1] += 1;
    heap.push(current);
  }
  let totalRatio = 0;
  for (const [passed, total] of heap.values) totalRatio += passed / total;
  return totalRatio / classes.length;
}

const maxAverageRatio = solve;
class Solution {
  maxAverageRatio(classes, extraStudents) { return solve(classes, extraStudents); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAverageRatio };
