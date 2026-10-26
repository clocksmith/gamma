'use strict';

// 2736. Maximum Sum Queries. Offline descending first coordinates with a reversed-coordinate Fenwick maximum; O((n+q) log(n+q)) time and O(n+q) space. Inputs are preserved.

function solve(nums1, nums2, queries) {
  const points = nums1.map((value, index) => [value, nums2[index]]).sort((a, b) => b[0] - a[0]);
  const coordinates = Array.from(new Set(nums2)).sort((a, b) => a - b);
  const size = coordinates.length;
  const tree = Array(size + 1).fill(-1);
  function lowerBound(value) {
    let low = 0;
    let high = size;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (coordinates[middle] < value) low = middle + 1;
      else high = middle;
    }
    return low;
  }
  const answer = Array(queries.length).fill(-1);
  const order = Array.from({ length: queries.length }, (_, index) => index).sort((a, b) => queries[b][0] - queries[a][0]);
  let used = 0;
  for (const index of order) {
    const [minimumFirst, minimumSecond] = queries[index];
    while (used < points.length && points[used][0] >= minimumFirst) {
      const [first, second] = points[used];
      const value = first + second;
      for (let position = size - lowerBound(second); position <= size; position += position & -position) tree[position] = Math.max(tree[position], value);
      used += 1;
    }
    let best = -1;
    for (let position = size - lowerBound(minimumSecond); position > 0; position -= position & -position) best = Math.max(best, tree[position]);
    answer[index] = best;
  }
  return answer;
}

const maximumSumQueries = solve;
class Solution {
  maximumSumQueries(nums1, nums2, queries) { return solve(nums1, nums2, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSumQueries };
