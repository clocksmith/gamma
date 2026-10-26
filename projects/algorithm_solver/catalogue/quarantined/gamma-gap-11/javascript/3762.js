'use strict';

// 3762. Minimum Operations to Equalize Subarrays.
// O((n + q) log n) time and O(n log n) space; persistent frequency/sum trees answer range medians.
function solve(nums, k, queries) {
  const scaled = nums.map(value => Math.floor(value / k));
  const values = [...new Set(scaled)].sort((left, right) => left - right);
  const rank = new Map(values.map((value, index) => [value, index]));
  const capacity = 1 + nums.length * (Math.ceil(Math.log2(values.length)) + 1);
  const leftChild = new Int32Array(capacity);
  const rightChild = new Int32Array(capacity);
  const count = new Int32Array(capacity);
  const sums = new Float64Array(capacity);
  let used = 1;
  function insert(previous, low, high, position, value) {
    const node = used;
    used += 1;
    leftChild[node] = leftChild[previous];
    rightChild[node] = rightChild[previous];
    count[node] = count[previous] + 1;
    sums[node] = sums[previous] + value;
    if (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      if (position <= middle) leftChild[node] = insert(leftChild[previous], low, middle, position, value);
      else rightChild[node] = insert(rightChild[previous], middle + 1, high, position, value);
    }
    return node;
  }
  const roots = [0];
  const breaks = new Int32Array(nums.length);
  for (let index = 0; index < nums.length; index += 1) {
    const value = scaled[index];
    roots.push(insert(roots[roots.length - 1], 0, values.length - 1, rank.get(value), value));
    if (index > 0) breaks[index] = breaks[index - 1] + (nums[index] % k !== nums[index - 1] % k ? 1 : 0);
  }
  const answer = [];
  for (const [start, end] of queries) {
    if (breaks[end] !== breaks[start]) {
      answer.push(-1);
      continue;
    }
    let old = roots[start];
    let current = roots[end + 1];
    const total = sums[current] - sums[old];
    const length = end - start + 1;
    let order = Math.floor((length + 1) / 2);
    let low = 0;
    let high = values.length - 1;
    let belowCount = 0;
    let belowSum = 0;
    while (low < high) {
      const middle = low + Math.floor((high - low) / 2);
      const oldLeft = leftChild[old];
      const currentLeft = leftChild[current];
      const amount = count[currentLeft] - count[oldLeft];
      if (order <= amount) {
        old = oldLeft;
        current = currentLeft;
        high = middle;
      } else {
        order -= amount;
        belowCount += amount;
        belowSum += sums[currentLeft] - sums[oldLeft];
        old = rightChild[old];
        current = rightChild[current];
        low = middle + 1;
      }
    }
    const median = values[low];
    answer.push(total - 2 * belowSum + median * (2 * belowCount - length));
  }
  return answer;
}

const minOperations = solve;
class Solution {
  minOperations(nums, k, queries) { return solve(nums, k, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
