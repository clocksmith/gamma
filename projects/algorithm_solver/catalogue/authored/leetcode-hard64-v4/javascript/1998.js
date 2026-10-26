'use strict';

// 1998. GCD Sort of an Array. Prime-factor connectivity and sorted-position comparison; O(M log log M+n log n+n log M*alpha(M)) time, O(M+n) space. Inputs are preserved.

class DisjointSet {
  constructor(size) {
    this.parent = Array.from({ length: size }, (_, index) => index);
    this.sizes = Array(size).fill(1);
  }
  find(node) {
    while (node !== this.parent[node]) {
      this.parent[node] = this.parent[this.parent[node]];
      node = this.parent[node];
    }
    return node;
  }
  union(left, right) {
    let a = this.find(left);
    let b = this.find(right);
    if (a === b) return;
    if (this.sizes[a] < this.sizes[b]) [a, b] = [b, a];
    this.parent[b] = a;
    this.sizes[a] += this.sizes[b];
  }
}

function solve(nums) {
  let maximum = 0;
  for (const value of nums) maximum = Math.max(maximum, value);
  const smallest = Array.from({ length: maximum + 1 }, (_, index) => index);
  for (let prime = 2; prime * prime <= maximum; prime += 1) {
    if (smallest[prime] === prime) {
      for (let multiple = prime * prime; multiple <= maximum; multiple += prime) {
        if (smallest[multiple] === multiple) smallest[multiple] = prime;
      }
    }
  }
  const sets = new DisjointSet(maximum + 1);
  for (const value of nums) {
    let remaining = value;
    while (remaining > 1) {
      const prime = smallest[remaining];
      sets.union(value, prime);
      while (remaining % prime === 0) remaining /= prime;
    }
  }
  const ordered = nums.slice().sort((a, b) => a - b);
  for (let index = 0; index < nums.length; index += 1) {
    if (sets.find(nums[index]) !== sets.find(ordered[index])) return false;
  }
  return true;
}

const gcdSort = solve;
class Solution {
  gcdSort(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, gcdSort };
