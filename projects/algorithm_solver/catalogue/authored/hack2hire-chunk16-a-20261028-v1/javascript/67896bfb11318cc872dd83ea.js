"use strict";
// Hack2Hire 67896bfb11318cc872dd83ea (Group Elements by Shared Properties) over an INFERRED spec; qualification unknown.

function solve(elements) {
  const n = elements.length;
  const parent = new Int32Array(n);
  for (let i = 0; i < n; i++) parent[i] = i;
  const find = (x) => {
    while (parent[x] !== x) {
      parent[x] = parent[parent[x]];
      x = parent[x];
    }
    return x;
  };
  for (const position of [1, 2, 3]) {
    const first = new Map();
    for (let i = 0; i < n; i++) {
      const value = elements[i][position];
      if (first.has(value)) {
        const a = find(first.get(value)), b = find(i);
        if (a !== b) parent[a] = b;
      } else first.set(value, i);
    }
  }
  const groups = new Map();
  for (let i = 0; i < n; i++) {
    const root = find(i);
    if (!groups.has(root)) groups.set(root, []);
    groups.get(root).push(elements[i][0]);
  }
  const out = [];
  for (const ids of groups.values()) {
    ids.sort((x, y) => x - y);
    out.push(ids);
  }
  out.sort((g, h) => g[0] - h[0]);
  return out;
}

function groupElements(elements) { return solve(elements); }

module.exports = solve;
module.exports.groupElements = groupElements;
