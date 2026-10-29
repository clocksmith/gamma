"use strict";
// Hack2Hire 6769dd5b11bbd512d60ce762 (Max Sum Between Leaf Nodes) over an INFERRED spec; qualification unknown.

function solve(tree) {
  const vals = [tree[0]], left = [-1], right = [-1];
  let queueHead = 0, i = 1;
  while (i < tree.length) {
    const parent = queueHead++;
    for (const side of [left, right]) {
      if (i < tree.length) {
        if (tree[i] !== null) {
          vals.push(tree[i]); left.push(-1); right.push(-1);
          side[parent] = vals.length - 1;
        }
        i++;
      }
    }
  }
  const n = vals.length, down = new Array(n).fill(0);
  let best = null, leaves = 0, leafValue = 0;
  for (let v = n - 1; v >= 0; v--) { // children always have larger level-order indices
    const l = left[v], r = right[v];
    if (l < 0 && r < 0) { down[v] = vals[v]; leaves++; leafValue = vals[v]; }
    else if (l < 0 || r < 0) down[v] = vals[v] + down[l >= 0 ? l : r];
    else {
      down[v] = vals[v] + Math.max(down[l], down[r]);
      const through = down[l] + down[r] + vals[v];
      if (best === null || through > best) best = through;
    }
  }
  return leaves === 1 ? leafValue : best;
}

function maxLeafToLeafSum(tree) { return solve(tree); }

module.exports = solve;
module.exports.maxLeafToLeafSum = maxLeafToLeafSum;
