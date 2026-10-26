'use strict';

// 3781. Maximum Score After Binary Swaps.
// O(n log n) time and O(n) space; each original one supplies a prefix deadline for its selected position.
class Heap {
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
    if (this.values.length === 0) return undefined;
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

function solve(nums, s) {
  const available = new Heap((left, right) => left > right);
  let answer = 0;
  for (let index = 0; index < nums.length; index += 1) {
    available.push(nums[index]);
    if (s[index] === '1') answer += available.pop();
  }
  return answer;
}

const maximumScore = solve;
class Solution {
  maximumScore(nums, s) { return solve(nums, s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };
