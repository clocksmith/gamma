"use strict";
// Hack2Hire 69e92eb7fbaf3da641828669 (Palindromic Storage Paths) over an INFERRED spec; qualification unknown.

function solve(arr, treeFrom, treeTo, queries) {
  const n = arr.length;
  const adj = Array.from({ length: n }, () => []);
  for (let i = 0; i < treeFrom.length; i++) { adj[treeFrom[i]].push(treeTo[i]); adj[treeTo[i]].push(treeFrom[i]); }
  const wanted = new Uint8Array(n);
  for (const q of queries) wanted[q] = 1;
  const answer = new Array(n).fill(0);
  const counts = new Map([[0, 1]]);
  const su = [0], sp = [-1], sm = [0], sl = [0];
  while (su.length) {
    const u = su.pop(), parent = sp.pop(), leaving = sl.pop();
    let mask = sm.pop();
    if (leaving) { counts.set(mask, counts.get(mask) - 1); continue; }
    mask ^= 1 << (arr[u].charCodeAt(0) - 97);
    if (wanted[u]) {
      let total = counts.get(mask) || 0;
      for (let bit = 0; bit < 26; bit++) total += counts.get(mask ^ (1 << bit)) || 0;
      answer[u] = total;
    }
    counts.set(mask, (counts.get(mask) || 0) + 1);
    su.push(u); sp.push(parent); sm.push(mask); sl.push(1);
    for (const v of adj[u]) if (v !== parent) { su.push(v); sp.push(u); sm.push(mask); sl.push(0); }
  }
  return queries.map((q) => answer[q]);
}

function palindromicPaths(arr, treeFrom, treeTo, queries) { return solve(arr, treeFrom, treeTo, queries); }

module.exports = solve;
module.exports.palindromicPaths = palindromicPaths;
