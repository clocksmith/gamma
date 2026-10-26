'use strict';

// 3859. Count Subarrays With K Distinct Integers.
// O(n log n) time and O(n) space; at-most-k window and the minimum mth-last occurrence among its active values.
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

function solve(nums, k, m) {
  const occurrences = new Map();
  const active = new Map();
  const latest = new Map();
  const heap = new Heap((left, right) => left[0] < right[0]);
  let left = 0;
  let answer = 0;
  for (let right = 0; right < nums.length; right += 1) {
    const value = nums[right];
    if (!occurrences.has(value)) occurrences.set(value, []);
    const positions = occurrences.get(value);
    positions.push(right);
    latest.set(value, right);
    active.set(value, (active.get(value) || 0) + 1);
    while (active.size > k) {
      const dropped = nums[left];
      const remaining = active.get(dropped) - 1;
      if (remaining === 0) active.delete(dropped);
      else active.set(dropped, remaining);
      left += 1;
    }
    const boundary = positions.length >= m ? positions[positions.length - m] : -1;
    heap.push([boundary, value, right]);
    while (heap.size > 0) {
      const [position, member, version] = heap.peek();
      if (active.has(member) && latest.get(member) === version) break;
      heap.pop();
    }
    if (active.size === k) answer += Math.max(0, heap.peek()[0] - left + 1);
  }
  return answer;
}

const countSubarrays = solve;
class Solution {
  countSubarrays(nums, k, m) { return solve(nums, k, m); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubarrays };
