'use strict';

// 630. Course Schedule III.

class _Heap {
  constructor(less = (a, b) => a < b) { this.data = []; this.less = less; }
  get size() { return this.data.length; }
  peek() { return this.data[0]; }
  push(value) {
    const a = this.data;
    let i = a.length;
    a.push(value);
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (!this.less(value, a[parent])) break;
      a[i] = a[parent];
      i = parent;
    }
    a[i] = value;
  }
  pop() {
    const a = this.data;
    if (a.length === 0) return undefined;
    const result = a[0];
    const last = a.pop();
    if (a.length > 0) {
      let i = 0;
      while (2 * i + 1 < a.length) {
        let child = 2 * i + 1;
        if (child + 1 < a.length && this.less(a[child + 1], a[child])) child += 1;
        if (!this.less(a[child], last)) break;
        a[i] = a[child];
        i = child;
      }
      a[i] = last;
    }
    return result;
  }
}

function solve(courses) {
  const heap = new _Heap((a, b) => a > b);
  let elapsed = 0;
  for (const [duration, deadline] of courses.slice().sort((a, b) => a[1] - b[1])) {
    elapsed += duration; heap.push(duration);
    if (elapsed > deadline) elapsed -= heap.pop();
  }
  return heap.size;
}

const scheduleCourse = solve;
class Solution {
  scheduleCourse(courses) { return solve(courses); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, scheduleCourse };
