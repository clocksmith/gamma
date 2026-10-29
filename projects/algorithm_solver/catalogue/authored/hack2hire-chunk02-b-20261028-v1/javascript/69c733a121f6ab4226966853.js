"use strict";
// Original Hack2Hire 69c733a121f6ab4226966853 variant over an INFERRED specification; qualification unknown.
function solve(nodes) {
  const out = [], stack = [0];
  while (stack.length) {
    const row = nodes[stack.pop()];
    out.push([row[0], row[1]]);
    for (let i = row.length - 1; i >= 2; i--) stack.push(row[i]);
  }
  return out;
}
function preorderTraversal(nodes) { return solve(nodes); }
module.exports = solve;
module.exports.preorderTraversal = preorderTraversal;
