'use strict';

// 2157. Groups of Strings. Union equal masks, deletion neighbors, and shared deletion signatures; O(L+26*n*alpha(n)) time, O(26*n) space. Inputs are preserved.

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

function solve(words) {
  const sets = new DisjointSet(words.length);
  const masks = [];
  const owners = new Map();
  for (let index = 0; index < words.length; index += 1) {
    let mask = 0;
    for (const character of words[index]) mask |= 1 << (character.charCodeAt(0) - 97);
    masks.push(mask);
    if (owners.has(mask)) sets.union(index, owners.get(mask));
    else owners.set(mask, index);
  }
  const removedOwners = new Map();
  for (let index = 0; index < masks.length; index += 1) {
    const mask = masks[index];
    let bits = mask;
    while (bits !== 0) {
      const bit = bits & -bits;
      bits ^= bit;
      const removed = mask ^ bit;
      if (owners.has(removed)) sets.union(index, owners.get(removed));
      if (removedOwners.has(removed)) sets.union(index, removedOwners.get(removed));
      else removedOwners.set(removed, index);
    }
  }
  const roots = new Set();
  let maximum = 0;
  for (let index = 0; index < words.length; index += 1) {
    const root = sets.find(index);
    roots.add(root);
    maximum = Math.max(maximum, sets.sizes[root]);
  }
  return [roots.size, maximum];
}

const groupStrings = solve;
class Solution {
  groupStrings(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, groupStrings };
