'use strict';

// 1834. Single-Threaded CPU: schedule available tasks by processing time and original index.
// O(n * log(n + 1)) time and O(n) auxiliary space; inputs are read-only.
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

function solve(tasks) {
  const ordered = tasks.map(([start, duration], index) => [start, duration, index]);
  ordered.sort((a, b) => a[0] - b[0] || a[2] - b[2]);
  const heap = new MinHeap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]));
  const result = [];
  let time = 0;
  let index = 0;
  while (index < ordered.length || heap.size) {
    if (!heap.size) time = Math.max(time, ordered[index][0]);
    while (index < ordered.length && ordered[index][0] <= time) {
      const [, duration, original] = ordered[index];
      heap.push([duration, original]);
      index += 1;
    }
    const [duration, original] = heap.pop();
    result.push(original);
    time += duration;
  }
  return result;
}

const getOrder = solve;
class Solution {
  getOrder(tasks) { return solve(tasks); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getOrder };
