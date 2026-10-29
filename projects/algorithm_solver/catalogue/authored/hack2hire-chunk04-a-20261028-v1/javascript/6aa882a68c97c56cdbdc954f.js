"use strict";
// Hack2Hire 6aa882a68c97c56cdbdc954f (Uniform Group Spanning Tree) over an INFERRED spec; qualification unknown.

// Binary min-heap over values compared by `less` (hole-based sifting).
class Heap {
  constructor(less, items) { this.less = less; this.a = items || []; for (let i = (this.a.length >> 1) - 1; i >= 0; i--) this.down(i); }
  get size() { return this.a.length; }
  push(x) {
    const a = this.a, less = this.less;
    let i = a.length;
    a.push(x);
    while (i > 0) { const p = (i - 1) >> 1, parent = a[p]; if (!less(x, parent)) break; a[i] = parent; i = p; }
    a[i] = x;
  }
  pop() { const a = this.a, top = a[0], last = a.pop(); if (a.length) { a[0] = last; this.down(0); } return top; }
  down(i) {
    const a = this.a, n = a.length, less = this.less, x = a[i];
    for (;;) {
      const l = 2 * i + 1;
      if (l >= n) break;
      let m = l;
      if (l + 1 < n && less(a[l + 1], a[l])) m = l + 1;
      if (!less(a[m], x)) break;
      a[i] = a[m];
      i = m;
    }
    a[i] = x;
  }
}

function solve(groups, rank) {
  const k = groups.length;
  if (k === 1) return [];
  let r = BigInt(rank);
  const pick = [];
  for (const group of groups) { const size = BigInt(group.length); pick.push(group[Number(r % size)]); r /= size; }
  const nodes = [], owner = [];
  groups.forEach((group, g) => { for (const x of group) { nodes.push(x); owner.push(g); } });
  const n = BigInt(nodes.length), code = [];
  for (let j = 0; j < k - 2; j++) { code.push(Number(r % n)); r /= n; }
  const degree = new Array(k).fill(1);
  for (const position of code) degree[owner[position]]++;
  const leaves = new Heap((x, y) => x < y, degree.map((d, g) => g).filter((g) => degree[g] === 1));
  const edges = [];
  for (const position of code) {
    const leaf = leaves.pop();
    degree[leaf] = 0;
    edges.push([pick[leaf], nodes[position]]);
    const g = owner[position];
    if (--degree[g] === 1) leaves.push(g);
  }
  const u = leaves.pop(), v = leaves.pop();
  edges.push([pick[u], pick[v]]);
  return edges;
}

function uniformSpanningTree(groups, rank) { return solve(groups, rank); }

module.exports = solve;
module.exports.uniformSpanningTree = uniformSpanningTree;
