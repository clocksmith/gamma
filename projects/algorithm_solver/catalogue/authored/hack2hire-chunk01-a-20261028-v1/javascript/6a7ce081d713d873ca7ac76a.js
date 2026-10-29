"use strict";
// Hack2Hire 6a7ce081d713d873ca7ac76a (Delete a Forest Subtree, variant 1) over an INFERRED spec; qualification unknown.
function solve(parentIndex, node) {
  const n = parentIndex.length, children = Array.from({length: n}, () => []);
  for (let child = 0; child < n; child++) if (parentIndex[child] !== child) children[parentIndex[child]].push(child);
  const result = parentIndex.slice(), stack = [node];
  result[node] = -1;
  while (stack.length) {
    for (const child of children[stack.pop()]) { result[child] = -1; stack.push(child); }
  }
  return result;
}
function deleteSubtree(parentIndex, node) { return solve(parentIndex, node); }
module.exports = solve;
module.exports.deleteSubtree = deleteSubtree;
