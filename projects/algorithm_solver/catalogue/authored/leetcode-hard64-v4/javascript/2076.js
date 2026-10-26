'use strict';

// 2076. Process Restricted Friend Requests. Union-find with pre-merge restriction checks; O((n+R*Q)*alpha(n)) time, O(n+Q) space. Inputs are preserved.

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

function solve(n, restrictions, requests) {
  const sets = new DisjointSet(n);
  const answer = [];
  for (const [first, second] of requests) {
    const left = sets.find(first);
    const right = sets.find(second);
    let allowed = true;
    if (left !== right) {
      for (const [bannedFirst, bannedSecond] of restrictions) {
        const a = sets.find(bannedFirst);
        const b = sets.find(bannedSecond);
        if ((a === left && b === right) || (a === right && b === left)) {
          allowed = false;
          break;
        }
      }
      if (allowed) sets.union(left, right);
    }
    answer.push(allowed);
  }
  return answer;
}

const friendRequests = solve;
class Solution {
  friendRequests(n, restrictions, requests) { return solve(n, restrictions, requests); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, friendRequests };
