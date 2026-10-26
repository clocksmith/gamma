'use strict';

// 3845. Maximum Subarray XOR with Bounded Range.
// O(n B + 2^B) time and O(n + 2^B) space, B=15; sliding extrema and a counted prefix-XOR trie.
function solve(nums, k) {
  const base = 2 ** 15;
  const counts = new Int32Array(2 * base);
  function change(value, delta) {
    for (let index = base + value; index > 0; index = Math.floor(index / 2)) counts[index] += delta;
  }
  function maximumXor(value) {
    let node = 1;
    let answer = 0;
    for (let bit = 14; bit >= 0; bit -= 1) {
      const direction = (value >> bit) & 1;
      const opposite = node * 2 + (direction ^ 1);
      if (counts[opposite] > 0) {
        answer |= 1 << bit;
        node = opposite;
      } else node = node * 2 + direction;
    }
    return answer;
  }
  const minimum = [];
  const maximum = [];
  let minHead = 0;
  let maxHead = 0;
  const prefix = [0];
  change(0, 1);
  let left = 0;
  let answer = 0;
  for (let right = 0; right < nums.length; right += 1) {
    const value = nums[right];
    prefix.push(prefix[prefix.length - 1] ^ value);
    while (minimum.length > minHead && nums[minimum[minimum.length - 1]] >= value) minimum.pop();
    while (maximum.length > maxHead && nums[maximum[maximum.length - 1]] <= value) maximum.pop();
    minimum.push(right);
    maximum.push(right);
    while (nums[maximum[maxHead]] - nums[minimum[minHead]] > k) {
      change(prefix[left], -1);
      if (minimum[minHead] === left) minHead += 1;
      if (maximum[maxHead] === left) maxHead += 1;
      left += 1;
    }
    answer = Math.max(answer, maximumXor(prefix[prefix.length - 1]));
    change(prefix[prefix.length - 1], 1);
  }
  return answer;
}

const maxXor = solve;
class Solution {
  maxXor(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxXor };
