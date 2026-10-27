'use strict';

// 502. IPO.

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

function solve(k, w, profits, capital) {
  const projects = capital.map((value, i) => [value, profits[i]]).sort((a, b) => a[0] - b[0]);
  const heap = new _Heap((a, b) => a > b);
  let index = 0;
  for (let step = 0; step < k; step += 1) {
    while (index < projects.length && projects[index][0] <= w) heap.push(projects[index++][1]);
    if (heap.size === 0) break;
    w += heap.pop();
  }
  return w;
}

const findMaximizedCapital = solve;
class Solution {
  findMaximizedCapital(k, w, profits, capital) { return solve(k, w, profits, capital); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaximizedCapital };
