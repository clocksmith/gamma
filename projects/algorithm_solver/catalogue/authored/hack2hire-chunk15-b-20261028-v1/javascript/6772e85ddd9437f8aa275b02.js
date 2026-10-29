"use strict";
// Hack2Hire 6772e85ddd9437f8aa275b02 (Find Path in N-ary Tree, variant 2 of 2) over an INFERRED spec; qualification unknown.

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
  const m = path.length;
  const fail = new Array(m).fill(0);
  let k = 0;
  for (let i = 1; i < m; i++) {
    while (k > 0 && path[i] !== path[k]) k = fail[k - 1];
    if (path[i] === path[k]) k++;
    fail[i] = k;
  }
  const memo = new Map();
  const inPath = new Set(path);
  // automaton transition from state (< m) on value, memoized per pair
  function step(state, value) {
    if (!inPath.has(value)) return 0;
    const chain = [];
    let result, key;
    for (;;) {
      key = state * 100001 + value;
      if (memo.has(key)) { result = memo.get(key); break; }
      if (path[state] === value) { result = state + 1; break; }
      if (state === 0) { result = 0; break; }
      chain.push(key);
      state = fail[state - 1];
    }
    memo.set(key, result);
    for (const c of chain) memo.set(c, result);
    return result;
  }
  const stack = [[0, 0]];
  while (stack.length) {
    const [v, state] = stack.pop();
    const s = step(state, values[v]);
    if (s === m) return true;
    for (const c of children[v]) stack.push([c, s]);
  }
  return false;
}

function pathExistsAnywhere(tree, path) { return solve(tree, path); }

module.exports = solve;
module.exports.pathExistsAnywhere = pathExistsAnywhere;
