"use strict";
// Hack2Hire 6775decc2c61a9f93e698ba0 (Find Longest Path in DAG) over an INFERRED spec; qualification unknown.

function solve(edges) {
  if (!edges.length) return [];
  const successors = new Map();
  const indegree = new Map();
  for (const [a, b] of edges) {
    if (!successors.has(a)) successors.set(a, []);
    if (!successors.has(b)) successors.set(b, []);
    successors.get(a).push(b);
    indegree.set(b, (indegree.get(b) || 0) + 1);
    if (!indegree.has(a)) indegree.set(a, 0);
  }
  const order = [];
  for (const v of successors.keys()) if (indegree.get(v) === 0) order.push(v);
  for (let i = 0; i < order.length; i++) {
    for (const w of successors.get(order[i])) {
      indegree.set(w, indegree.get(w) - 1);
      if (indegree.get(w) === 0) order.push(w);
    }
  }
  const length = new Map();
  const following = new Map();
  for (let i = order.length - 1; i >= 0; i--) {
    const v = order[i];
    let best = 0;
    let choice = null;
    for (const w of successors.get(v)) {
      const candidate = length.get(w) + 1;
      if (candidate > best || (candidate === best && w < choice)) { best = candidate; choice = w; }
    }
    length.set(v, best);
    following.set(v, choice);
  }
  let start = null;
  for (const v of successors.keys()) {
    if (start === null || length.get(v) > length.get(start) || (length.get(v) === length.get(start) && v < start)) start = v;
  }
  const path = [start];
  while (following.get(path[path.length - 1]) !== null) path.push(following.get(path[path.length - 1]));
  return path;
}

function longestPath(edges) { return solve(edges); }

module.exports = solve;
module.exports.longestPath = longestPath;
