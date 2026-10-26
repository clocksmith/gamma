'use strict';

// 1775. Equal Sum Arrays With Minimum Number of Operations: spend the largest available per-element sum improvements first.
// O(n + m) time and O(1) auxiliary space for values from 1 through 6; inputs are read-only.
function solve(nums1, nums2) {
  if (nums1.length > 6 * nums2.length || nums2.length > 6 * nums1.length) return -1;
  let low = nums1;
  let high = nums2;
  let lowSum = 0;
  let highSum = 0;
  for (const value of low) lowSum += value;
  for (const value of high) highSum += value;
  if (lowSum > highSum) {
    [low, high] = [high, low];
    [lowSum, highSum] = [highSum, lowSum];
  }
  let difference = highSum - lowSum;
  const gains = new Array(6).fill(0);
  for (const value of low) gains[6 - value] += 1;
  for (const value of high) gains[value - 1] += 1;
  let answer = 0;
  for (let gain = 5; gain >= 1; gain -= 1) {
    if (difference <= 0) return answer;
    const count = Math.min(gains[gain], Math.ceil(difference / gain));
    difference -= count * gain;
    answer += count;
  }
  return difference <= 0 ? answer : -1;
}

const minOperations = solve;
class Solution {
  minOperations(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
