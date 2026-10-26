'use strict';

// 2179. Count Good Triplets in an Array. Permutation positions and a Fenwick prefix count; O(n log n) time and O(n) space. Inputs are preserved.

function solve(nums1, nums2) {
  const size = nums1.length;
  const positions = new Int32Array(size);
  for (let index = 0; index < size; index += 1) positions[nums2[index]] = index;
  const tree = new Int32Array(size + 1);
  let answer = 0;
  for (let index = 0; index < size; index += 1) {
    const position = positions[nums1[index]];
    let cursor = position;
    let earlierSmaller = 0;
    while (cursor > 0) {
      earlierSmaller += tree[cursor];
      cursor -= cursor & -cursor;
    }
    const laterLarger = size - 1 - position - (index - earlierSmaller);
    answer += earlierSmaller * laterLarger;
    cursor = position + 1;
    while (cursor <= size) {
      tree[cursor] += 1;
      cursor += cursor & -cursor;
    }
  }
  return answer;
}

const goodTriplets = solve;
class Solution {
  goodTriplets(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, goodTriplets };
