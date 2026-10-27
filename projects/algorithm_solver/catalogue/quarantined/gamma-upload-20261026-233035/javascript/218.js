'use strict';
// 218. The Skyline Problem.
class Heap {
  constructor(compare) { this.data = []; this.compare = compare; }
  push(value) {
    const data = this.data; data.push(value); let index = data.length - 1;
    while (index) { const parent = Math.floor((index - 1) / 2); if (!this.compare(data[index], data[parent])) break;
      [data[index], data[parent]] = [data[parent], data[index]]; index = parent; }
  }
  pop() {
    const top = this.data[0]; const last = this.data.pop();
    if (this.data.length) { this.data[0] = last; let index = 0;
      while (true) { let best = index; const left = index * 2 + 1; const right = left + 1;
        if (left < this.data.length && this.compare(this.data[left], this.data[best])) best = left;
        if (right < this.data.length && this.compare(this.data[right], this.data[best])) best = right;
        if (best === index) break; [this.data[index], this.data[best]] = [this.data[best], this.data[index]]; index = best; } }
    return top;
  }
  peek() { return this.data[0]; }
}
function solve(buildings) {
  const events = [];
  for (const [left, right, height] of buildings) { events.push([left, -height, right], [right, 0, 0]); }
  events.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const heap = new Heap((a, b) => a[0] < b[0]);
  heap.push([0, Infinity]);
  const result = [];
  for (const [x, negativeHeight, right] of events) {
    while (heap.peek()[1] <= x) heap.pop();
    if (negativeHeight !== 0) heap.push([negativeHeight, right]);
    const height = -heap.peek()[0];
    if (!result.length || result[result.length - 1][1] !== height) result.push([x, height]);
  }
  return result;
}
const getSkyline = solve;
class Solution { getSkyline(buildings) { return solve(buildings); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getSkyline };
