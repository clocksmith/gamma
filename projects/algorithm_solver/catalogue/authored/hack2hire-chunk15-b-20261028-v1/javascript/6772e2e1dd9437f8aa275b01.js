"use strict";
// Hack2Hire 6772e2e1dd9437f8aa275b01 (Find Path in N-ary Tree, variant 1 of 2) over an INFERRED spec; qualification unknown.

function parse(tree) {
  const values = [tree[0]], children = [[]];
  let parent = -1;
  for (let i = 1; i < tree.length; i++) {
    if (tree[i] === null) {
      parent++;
    } else {
      children[parent].push(values.length);
      values.push(tree[i]);
      children.push([]);
    }
  }
  return [values, children];
}

function solve(tree, path) {
  const [values, children] = parse(tree);
  if (values[0] !== path[0]) return false;
  let frontier = [0];
  for (let i = 1; i < path.length; i++) {
    const next = [];
    for (const v of frontier) for (const c of children[v]) if (values[c] === path[i]) next.push(c);
    if (!next.length) return false;
    frontier = next;
  }
  return true;
}

function pathExists(tree, path) { return solve(tree, path); }

module.exports = solve;
module.exports.pathExists = pathExists;
