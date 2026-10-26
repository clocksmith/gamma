'use strict';

// 2948. Make Lexicographically Smallest Array by Swapping Elements: assign each connected value group in sorted order to its sorted original positions.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, limit) {
  const ordered = nums.map((value, index) => [value, index])
    .sort((left, right) => left[0] - right[0] || left[1] - right[1]);
  const result = new Array(nums.length);
  let left = 0;
  while (left < nums.length) {
    let right = left + 1;
    while (right < nums.length && ordered[right][0] - ordered[right - 1][0] <= limit) right += 1;
    const indices = [];
    for (let index = left; index < right; index += 1) indices.push(ordered[index][1]);
    indices.sort((a, b) => a - b);
    for (let offset = 0; offset < indices.length; offset += 1) {
      result[indices[offset]] = ordered[left + offset][0];
    }
    left = right;
  }
  return result;
}

const lexicographicallySmallestArray = solve;
class Solution {
  lexicographicallySmallestArray(nums, limit) { return solve(nums, limit); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lexicographicallySmallestArray };
