'use strict';

// 608. Tree Node. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. tree: id, p_id (nullable). Output: id, type. Root classification takes precedence over leaf classification.

function solve(tree) {
  const parents = new Set(tree.filter(row => row.p_id != null).map(row => row.p_id));
  return tree.slice().sort((a, b) => a.id - b.id).map(row => ({id: row.id, type: row.p_id == null ? 'Root' : parents.has(row.id) ? 'Inner' : 'Leaf'}));
}

const treeNode = solve;
class Solution {
  treeNode(tree) { return solve(tree); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, treeNode };
