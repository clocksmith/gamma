'use strict';

// 3695. Maximize Alternating Sum Using Swaps.
// O(n log n + e * alpha(n)) time and O(n) auxiliary space; caller arrays are preserved.
function solve(nums, swaps) {
  const n = nums.length;
  const parent = Array.from({ length: n }, (_, index) => index);
  const size = new Int32Array(n).fill(1);
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  for (const pair of swaps) {
    let left = find(pair[0]);
    let right = find(pair[1]);
    if (left === right) continue;
    if (size[left] < size[right]) [left, right] = [right, left];
    parent[right] = left;
    size[left] += size[right];
  }
  const groups = new Map();
  const even = new Int32Array(n);
  for (let index = 0; index < n; index += 1) {
    const root = find(index);
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root).push(nums[index]);
    if (index % 2 === 0) even[root] += 1;
  }
  let answer = 0;
  for (const [root, values] of groups) {
    values.sort((left, right) => right - left);
    for (let index = 0; index < values.length; index += 1) {
      answer += index < even[root] ? values[index] : -values[index];
    }
  }
  return answer;
}

const maxAlternatingSum = solve;
class Solution {
  maxAlternatingSum(nums, swaps) { return solve(nums, swaps); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxAlternatingSum };
