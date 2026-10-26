'use strict';

// 1675. Minimize Deviation in Array: normalize odd values, then reduce the maximum; O(n*log(n+1)*log(M+1)) time and O(n) space.

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

function solve(nums) {
  const heap = new _MinHeap();
  let minimum = Infinity;
  for (const original of nums) {
    const value = original % 2 === 0 ? original : original * 2;
    minimum = Math.min(minimum, value);
    heap.push(-value);
  }
  let answer = Infinity;
  while (heap.size > 0) {
    let maximum = -heap.pop();
    answer = Math.min(answer, maximum - minimum);
    if (maximum % 2 !== 0) break;
    maximum /= 2;
    minimum = Math.min(minimum, maximum);
    heap.push(-maximum);
  }
  return answer;
}

const minimumDeviation = solve;
class Solution {
  minimumDeviation(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumDeviation };
