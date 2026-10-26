'use strict';

// 2818. Apply Operations to Maximize Score. Count prime-score ownership intervals, then take the largest available factors; O(M log log(M+2)+n log n+n log(k+1)) time and O(M+n) space, M=max(nums). Inputs are preserved.

function solve(nums, k) {
  const modulus = 1000000007n;
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const scores = Array(maximum + 1).fill(0);
  for (let prime = 2; prime <= maximum; prime += 1) {
    if (scores[prime] !== 0) continue;
    for (let multiple = prime; multiple <= maximum; multiple += prime) scores[multiple] += 1;
  }
  const size = nums.length;
  const left = Array(size).fill(-1);
  const right = Array(size).fill(size);
  const stack = [];
  for (let index = 0; index < size; index += 1) {
    while (stack.length > 0 && scores[nums[stack[stack.length - 1]]] < scores[nums[index]]) stack.pop();
    if (stack.length > 0) left[index] = stack[stack.length - 1];
    stack.push(index);
  }
  stack.length = 0;
  for (let index = size - 1; index >= 0; index -= 1) {
    while (stack.length > 0 && scores[nums[stack[stack.length - 1]]] <= scores[nums[index]]) stack.pop();
    if (stack.length > 0) right[index] = stack[stack.length - 1];
    stack.push(index);
  }
  function power(base, exponent) {
    let result = 1n;
    let value = BigInt(base);
    while (exponent > 0) {
      if (exponent % 2 === 1) result = result * value % modulus;
      value = value * value % modulus;
      exponent = Math.floor(exponent / 2);
    }
    return result;
  }
  const order = Array.from({ length: size }, (_, index) => index).sort((a, b) => nums[b] - nums[a]);
  let answer = 1n;
  let remaining = k;
  for (const index of order) {
    const uses = Math.min(remaining, (index - left[index]) * (right[index] - index));
    answer = answer * power(nums[index], uses) % modulus;
    remaining -= uses;
    if (remaining === 0) break;
  }
  return Number(answer);
}

const maximumScore = solve;
class Solution {
  maximumScore(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumScore };
