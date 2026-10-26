'use strict';

// 2382. Maximum Segment Sum After Removals. Reverse removals and merge active adjacent components; O(n*alpha(n)) time and O(n) space. Inputs are preserved.

function solve(nums, removeQueries) {
  const size = nums.length;
  const parent = Array.from({ length: size }, (_, index) => index);
  const weight = Array(size).fill(1);
  const totals = Array(size).fill(0);
  const active = Array(size).fill(false);
  const answer = Array(size).fill(0);
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  function merge(first, second) {
    first = find(first);
    second = find(second);
    if (first === second) return;
    if (weight[first] < weight[second]) [first, second] = [second, first];
    parent[second] = first;
    weight[first] += weight[second];
    totals[first] += totals[second];
  }
  let largest = 0;
  for (let step = size - 1; step >= 0; step -= 1) {
    answer[step] = largest;
    const node = removeQueries[step];
    active[node] = true;
    totals[node] = nums[node];
    if (node > 0 && active[node - 1]) merge(node, node - 1);
    if (node + 1 < size && active[node + 1]) merge(node, node + 1);
    largest = Math.max(largest, totals[find(node)]);
  }
  return answer;
}

const maximumSegmentSum = solve;
class Solution {
  maximumSegmentSum(nums, removeQueries) { return solve(nums, removeQueries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumSegmentSum };
