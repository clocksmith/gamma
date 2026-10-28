'use strict';

// 3310. Remove Methods From Project (Medium).
// Specification: https://leetcode.com/problems/remove-methods-from-project/description/
function solve(n, k, invocations) {
  const adj = Array.from({ length: n }, () => []);
  for (const [a, b] of invocations) adj[a].push(b);
  const suspicious = new Set([k]);
  const stack = [k];
  while (stack.length) {
    const u = stack.pop();
    for (const v of adj[u]) {
      if (!suspicious.has(v)) { suspicious.add(v); stack.push(v); }
    }
  }
  for (const [a, b] of invocations) {
    if (!suspicious.has(a) && suspicious.has(b)) {
      return Array.from({ length: n }, (_, i) => i);
    }
  }
  const out = [];
  for (let i = 0; i < n; i++) if (!suspicious.has(i)) out.push(i);
  return out;
}
const remainingMethods = solve;
class Solution { remainingMethods(n, k, invocations) { return solve(n, k, invocations); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, remainingMethods };
