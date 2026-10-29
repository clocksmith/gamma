"use strict";
// Hack2Hire 6a7ceda7d713d873ca7ac7f8 (Delete a Forest Subtree, variant 2) over an INFERRED spec; qualification unknown.
function solve(parentIndex, nodes) {
  const n = parentIndex.length, children = Array.from({length: n}, () => []);
  for (let child = 0; child < n; child++) if (parentIndex[child] !== child) children[parentIndex[child]].push(child);
  const result = parentIndex.slice();
  for (const node of nodes) {
    if (result[node] === -1) continue; // already deleted with its subtree
    result[node] = -1;
    const stack = [node];
    while (stack.length) {
      for (const child of children[stack.pop()]) {
        if (result[child] !== -1) { result[child] = -1; stack.push(child); }
      }
    }
  }
  return result;
}
function deleteSubtrees(parentIndex, nodes) { return solve(parentIndex, nodes); }
module.exports = solve;
module.exports.deleteSubtrees = deleteSubtrees;
