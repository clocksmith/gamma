'use strict';

// 703. Kth Largest Element in a Stream.

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

class KthLargest {
  constructor(k, nums) { this.k = k; this.heap = new _Heap(); for (const value of nums) this.add(value); }
  add(val) { this.heap.push(val); if (this.heap.size > this.k) this.heap.pop(); return this.heap.peek(); }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new KthLargest(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = KthLargest;

if (typeof module !== 'undefined') module.exports = { solve, KthLargest, Solution };
