'use strict';

// 632. Smallest Range Covering Elements from K Lists.

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

function solve(nums) {
  const heap = new _Heap((a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]));
  let maximum = -Infinity;
  for (let row = 0; row < nums.length; row += 1) {
    heap.push([nums[row][0], row, 0]); maximum = Math.max(maximum, nums[row][0]);
  }
  let answer = [heap.peek()[0], maximum];
  while (heap.size > 0) {
    const [minimum, row, index] = heap.pop();
    if (maximum - minimum < answer[1] - answer[0] || (maximum - minimum === answer[1] - answer[0] && minimum < answer[0])) answer = [minimum, maximum];
    if (index + 1 === nums[row].length) break;
    const value = nums[row][index + 1];
    maximum = Math.max(maximum, value); heap.push([value, row, index + 1]);
  }
  return answer;
}

const smallestRange = solve;
class Solution {
  smallestRange(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestRange };
