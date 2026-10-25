'use strict';

// 798. Smallest Rotation with Highest Score.
// O(n) time and space. The original array is never rotated or modified.
function solve(nums) {
  const size = nums.length;
  const changes = new Int32Array(size + 1);
  for (let index = 0; index < size; index += 1) {
    const value = nums[index];
    if (value === 0) continue;
    const left = (index - value + 1 + size) % size;
    const right = (index + 1) % size;
    if (left < right) {
      changes[left] += 1;
      changes[right] -= 1;
    } else {
      changes[0] += 1;
      changes[right] -= 1;
      changes[left] += 1;
      changes[size] -= 1;
    }
  }
  let bad = 0;
  let bestBad = size + 1;
  let answer = 0;
  for (let rotation = 0; rotation < size; rotation += 1) {
    bad += changes[rotation];
    if (bad < bestBad) {
      bestBad = bad;
      answer = rotation;
    }
  }
  return answer;
}

const bestRotation = solve;
class Solution {
  bestRotation(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, bestRotation };
