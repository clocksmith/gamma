'use strict';

// 2709. Greatest Common Divisor Traversal.
// O(M log log M + n log M*alpha(n)) time, O(M+n) space; factor private scalar copies.
function solve(nums) {
  const size = nums.length;
  if (size === 1) return true;
  let maximum = 0;
  for (const value of nums) {
    if (value === 1) return false;
    maximum = Math.max(maximum, value);
  }
  const smallest = new Int32Array(maximum + 1);
  for (let value = 0; value <= maximum; value += 1) smallest[value] = value;
  for (let prime = 2; prime * prime <= maximum; prime += 1) {
    if (smallest[prime] !== prime) continue;
    for (let multiple = prime * prime; multiple <= maximum; multiple += prime) {
      if (smallest[multiple] === multiple) smallest[multiple] = prime;
    }
  }
  const parent = Int32Array.from({ length: size }, (_, index) => index);
  const weight = new Int32Array(size).fill(1);
  function find(node) {
    while (parent[node] !== node) {
      parent[node] = parent[parent[node]];
      node = parent[node];
    }
    return node;
  }
  function unite(first, second) {
    first = find(first);
    second = find(second);
    if (first === second) return;
    if (weight[first] < weight[second]) [first, second] = [second, first];
    parent[second] = first;
    weight[first] += weight[second];
  }
  const owner = new Map();
  for (let index = 0; index < size; index += 1) {
    let remaining = nums[index];
    while (remaining > 1) {
      const prime = smallest[remaining];
      if (owner.has(prime)) unite(index, owner.get(prime));
      else owner.set(prime, index);
      while (remaining % prime === 0) remaining /= prime;
    }
  }
  const root = find(0);
  for (let index = 1; index < size; index += 1) if (find(index) !== root) return false;
  return true;
}

const canTraverseAllPairs = solve;
class Solution {
  canTraverseAllPairs(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canTraverseAllPairs };
