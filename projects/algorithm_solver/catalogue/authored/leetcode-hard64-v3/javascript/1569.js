'use strict';

// 1569. Number of Ways to Reorder Array to Get Same BST: iterative BST construction and subtree interleavings; O(n^2) time and O(n) space; exact modular products.

function solve(nums) {
  const modulus = 1000000007n;
  const size = nums.length;
  const left = Array(size).fill(-1);
  const right = Array(size).fill(-1);
  for (let index = 1; index < size; index += 1) {
    let node = 0;
    while (true) {
      const children = nums[index] < nums[node] ? left : right;
      if (children[node] === -1) { children[node] = index; break; }
      node = children[node];
    }
  }
  function power(base, exponent) {
    let answer = 1n;
    while (exponent > 0n) {
      if ((exponent & 1n) !== 0n) answer = answer * base % modulus;
      base = base * base % modulus;
      exponent >>= 1n;
    }
    return answer;
  }
  const factorial = Array(size + 1).fill(1n);
  for (let index = 1; index <= size; index += 1) factorial[index] = factorial[index - 1] * BigInt(index) % modulus;
  const inverse = Array(size + 1).fill(1n);
  inverse[size] = power(factorial[size], modulus - 2n);
  for (let index = size; index > 0; index -= 1) inverse[index - 1] = inverse[index] * BigInt(index) % modulus;
  const counts = Array(size).fill(0);
  const ways = Array(size).fill(1n);
  for (let node = size - 1; node >= 0; node -= 1) {
    const leftSize = left[node] === -1 ? 0 : counts[left[node]];
    const rightSize = right[node] === -1 ? 0 : counts[right[node]];
    let interleavings = factorial[leftSize + rightSize] * inverse[leftSize] % modulus * inverse[rightSize] % modulus;
    if (left[node] !== -1) interleavings = interleavings * ways[left[node]] % modulus;
    if (right[node] !== -1) interleavings = interleavings * ways[right[node]] % modulus;
    counts[node] = leftSize + rightSize + 1;
    ways[node] = interleavings;
  }
  return Number((ways[0] - 1n + modulus) % modulus);
}

const numOfWays = solve;
class Solution {
  numOfWays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfWays };
