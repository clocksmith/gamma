'use strict';

// 1705. Maximum Number of Eaten Apples: eat the earliest-expiring apple and batch the remaining days after arrivals stop.
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

function solve(apples, days) {
  const heap = new MinHeap((a, b) => a[0] < b[0]);
  let eaten = 0;
  for (let day = 0; day < apples.length; day += 1) {
    if (apples[day] > 0 && days[day] > 0) heap.push([day + days[day], apples[day]]);
    while (heap.size && heap.peek()[0] <= day) heap.pop();
    if (heap.size) {
      const [expiry, count] = heap.pop();
      eaten += 1;
      if (count > 1) heap.push([expiry, count - 1]);
    }
  }
  let day = apples.length;
  while (heap.size) {
    const [expiry, count] = heap.pop();
    if (expiry <= day) continue;
    const taken = Math.min(count, expiry - day);
    eaten += taken;
    day += taken;
  }
  return eaten;
}

const eatenApples = solve;
class Solution {
  eatenApples(apples, days) { return solve(apples, days); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, eatenApples };
