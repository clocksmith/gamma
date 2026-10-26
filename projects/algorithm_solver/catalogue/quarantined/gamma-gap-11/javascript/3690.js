'use strict';

// 3690. Split and Merge Array Transformation.
// O(n! * n^4) time and O(n! * n) space, with n <= 6; inputs are preserved.
function solve(nums1, nums2) {
  const target = nums2.join(',');
  const start = nums1.slice();
  const firstKey = start.join(',');
  if (firstKey === target) return 0;
  const queue = [[start, 0]];
  const seen = new Set([firstKey]);
  const n = start.length;
  for (let head = 0; head < queue.length; head += 1) {
    const [state, distance] = queue[head];
    for (let left = 0; left < n; left += 1) {
      for (let right = left + 1; right <= n; right += 1) {
        const block = state.slice(left, right);
        const rest = state.slice(0, left).concat(state.slice(right));
        for (let position = 0; position <= rest.length; position += 1) {
          const following = rest.slice(0, position).concat(block, rest.slice(position));
          const key = following.join(',');
          if (key === target) return distance + 1;
          if (!seen.has(key)) {
            seen.add(key);
            queue.push([following, distance + 1]);
          }
        }
      }
    }
  }
  return -1;
}

const minSplitMerge = solve;
class Solution {
  minSplitMerge(nums1, nums2) { return solve(nums1, nums2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSplitMerge };
