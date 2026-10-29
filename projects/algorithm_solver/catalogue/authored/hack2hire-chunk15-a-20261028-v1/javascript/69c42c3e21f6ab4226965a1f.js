"use strict";
// Hack2Hire 69c42c3e21f6ab4226965a1f (Copy Neighbor Sums Between Binary Trees) over an INFERRED spec; qualification unknown.

function decode(tree) {
  if (!tree.length) return [[], [], []];
  const values = [tree[0]], left = [-1], right = [-1];
  let node = 0, i = 1;
  while (node < values.length && i < tree.length) {
    for (const side of [left, right]) {
      if (i < tree.length) {
        if (tree[i] !== null) {
          side[node] = values.length;
          values.push(tree[i]); left.push(-1); right.push(-1);
        }
        i++;
      }
    }
    node++;
  }
  return [values, left, right];
}

function solve(trees) {
  const [values, left, right] = decode(trees[trees.length - 1]);
  for (let t = 0; t < trees.length - 1; t++) {
    const [sv, sl, sr] = decode(trees[t]);
    if (!sv.length) continue;
    if (!values.length) { values.push(0); left.push(-1); right.push(-1); }
    const pairs = [[0, 0]];
    for (let head = 0; head < pairs.length; head++) {
      const [s, d] = pairs[head];
      values[d] += sv[s] + (sl[s] >= 0 ? sv[sl[s]] : 0) + (sr[s] >= 0 ? sv[sr[s]] : 0);
      for (const [sourceSide, targetSide] of [[sl, left], [sr, right]]) {
        const child = sourceSide[s];
        if (child >= 0) {
          if (targetSide[d] < 0) {
            targetSide[d] = values.length;
            values.push(0); left.push(-1); right.push(-1);
          }
          pairs.push([child, targetSide[d]]);
        }
      }
    }
  }
  if (!values.length) return [];
  const out = [values[0]], queue = [0];
  for (let head = 0; head < queue.length; head++) {
    const node = queue[head];
    for (const child of [left[node], right[node]]) {
      if (child >= 0) { out.push(values[child]); queue.push(child); } else out.push(null);
    }
  }
  while (out[out.length - 1] === null) out.pop();
  return out;
}

function copyNeighborSums(trees) { return solve(trees); }

module.exports = solve;
module.exports.copyNeighborSums = copyNeighborSums;
