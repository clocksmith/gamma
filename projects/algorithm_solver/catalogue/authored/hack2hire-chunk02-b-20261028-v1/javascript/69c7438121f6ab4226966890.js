"use strict";
// Original Hack2Hire 69c7438121f6ab4226966890 variant over an INFERRED specification; qualification unknown.
function solve(nodesA, nodesB) {
  const out = [], stack = [[0, 0, -1]];
  while (stack.length) {
    const [a, b, parent] = stack.pop();
    const source = a !== null ? nodesA[a] : nodesB[b];
    const value = (a !== null ? nodesA[a][1] : 0) + (b !== null ? nodesB[b][1] : 0);
    const index = out.length;
    out.push([source[0], value]);
    if (parent >= 0) out[parent].push(index);
    const bByKey = new Map();
    if (b !== null) for (let i = 2; i < nodesB[b].length; i++) bByKey.set(nodesB[nodesB[b][i]][0], nodesB[b][i]);
    const pairs = [];
    if (a !== null) {
      for (let i = 2; i < nodesA[a].length; i++) {
        const c = nodesA[a][i], key = nodesA[c][0];
        pairs.push([c, bByKey.has(key) ? bByKey.get(key) : null]);
        bByKey.delete(key);
      }
    }
    if (b !== null) for (let i = 2; i < nodesB[b].length; i++) { const c = nodesB[b][i]; if (bByKey.has(nodesB[c][0])) pairs.push([null, c]); }
    for (let i = pairs.length - 1; i >= 0; i--) stack.push([pairs[i][0], pairs[i][1], index]);
  }
  return out;
}
function mergeTrees(nodesA, nodesB) { return solve(nodesA, nodesB); }
module.exports = solve;
module.exports.mergeTrees = mergeTrees;
