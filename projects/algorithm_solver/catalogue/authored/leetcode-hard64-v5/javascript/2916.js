'use strict';

// 2916. Subarrays Distinct Element Sum of Squares II. Maintain distinct-count range increments with two Fenwick trees; O(n log n) time and O(n) space. Inputs are preserved.

function solve(nums) {
  const modulus = 1000000007;
  const size = nums.length;
  const slope = Array(size + 2).fill(0);
  const offset = Array(size + 2).fill(0);
  function add(tree, index, delta) {
    while (index <= size + 1) { tree[index] += delta; index += index & -index; }
  }
  function prefix(tree, index) {
    let total = 0;
    while (index > 0) { total += tree[index]; index -= index & -index; }
    return total;
  }
  function sumThrough(index) {
    return prefix(slope, index) * index - prefix(offset, index);
  }
  const previous = new Map();
  let ending = 0;
  let answer = 0;
  for (let index = 0; index < size; index += 1) {
    const value = nums[index];
    const left = (previous.has(value) ? previous.get(value) : -1) + 2;
    const right = index + 1;
    const oldSum = sumThrough(right) - sumThrough(left - 1);
    ending = (ending + 2 * oldSum + right - left + 1) % modulus;
    answer = (answer + ending) % modulus;
    add(slope, left, 1);
    add(slope, right + 1, -1);
    add(offset, left, left - 1);
    add(offset, right + 1, -right);
    previous.set(value, index);
  }
  return answer;
}

const sumCounts = solve;
class Solution {
  sumCounts(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumCounts };
