'use strict';

// 2532. Time to Cross a Bridge. Event simulation with separate waiting and working heaps on both banks; O((n+k) log(k+1)) time and O(k) space. Inputs are preserved.

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
    const result = items[0];
    const value = items.pop();
    if (items.length === 0) return result;
    let index = 0;
    while (2 * index + 1 < items.length) {
      let child = 2 * index + 1;
      if (child + 1 < items.length && this.less(items[child + 1], items[child])) child += 1;
      if (!this.less(items[child], value)) break;
      items[index] = items[child];
      index = child;
    }
    items[index] = value;
    return result;
  }
}

function solve(n, k, time) {
  const priority = (a, b) => {
    const first = time[a][0] + time[a][2];
    const second = time[b][0] + time[b][2];
    return first > second || (first === second && a > b);
  };
  const chronological = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
  const waitingLeft = new MinHeap(priority);
  const waitingRight = new MinHeap(priority);
  const workingLeft = new MinHeap(chronological);
  const workingRight = new MinHeap(chronological);
  for (let worker = 0; worker < k; worker += 1) waitingLeft.push(worker);
  let remaining = n;
  let clock = 0;
  while (remaining > 0 || waitingRight.size > 0 || workingRight.size > 0) {
    while (workingLeft.size > 0 && workingLeft.peek()[0] <= clock) waitingLeft.push(workingLeft.pop()[1]);
    while (workingRight.size > 0 && workingRight.peek()[0] <= clock) waitingRight.push(workingRight.pop()[1]);
    if (waitingRight.size > 0) {
      const worker = waitingRight.pop();
      clock += time[worker][2];
      workingLeft.push([clock + time[worker][3], worker]);
    } else if (remaining > 0 && waitingLeft.size > 0) {
      const worker = waitingLeft.pop();
      clock += time[worker][0];
      remaining -= 1;
      workingRight.push([clock + time[worker][1], worker]);
    } else {
      const nextLeft = remaining > 0 && workingLeft.size > 0 ? workingLeft.peek()[0] : Infinity;
      const nextRight = workingRight.size > 0 ? workingRight.peek()[0] : Infinity;
      clock = Math.min(nextLeft, nextRight);
    }
  }
  return clock;
}

const findCrossingTime = solve;
class Solution {
  findCrossingTime(n, k, time) { return solve(n, k, time); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findCrossingTime };
