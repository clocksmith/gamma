'use strict';

// 3378. Count Connected Components in LCM Graph: union input indices that share a multiple within the threshold.
// O(n + T log T * alpha(n)) time and O(n + T) auxiliary space, T=threshold. Inputs are preserved.
function solve(nums, threshold) {
  const n = nums.length;
  const parent = Int32Array.from({ length: n }, (_, index) => index);
  const size = new Int32Array(n).fill(1);
  const owner = new Int32Array(threshold + 1).fill(-1);
  let components = n;
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  for (let index = 0; index < n; index += 1) {
    const value = nums[index];
    if (value > threshold) continue;
    for (let multiple = value; multiple <= threshold; multiple += value) {
      if (owner[multiple] === -1) {
        owner[multiple] = index;
      } else {
        let first = find(index);
        let second = find(owner[multiple]);
        if (first === second) continue;
        if (size[first] < size[second]) [first, second] = [second, first];
        parent[second] = first;
        size[first] += size[second];
        components -= 1;
      }
    }
  }
  return components;
}

const countComponents = solve;
class Solution {
  countComponents(nums, threshold) { return solve(nums, threshold); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countComponents };
