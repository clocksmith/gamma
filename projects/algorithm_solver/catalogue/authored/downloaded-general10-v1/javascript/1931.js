'use strict';

// 1931. Painting a Grid With Three Different Colors (Hard).
// Specification: https://leetcode.com/problems/painting-a-grid-with-three-different-colors/description/
function solve(m, n) {
  const mod = 1000000007;
  const states = [];
  function build(state) {
    if (state.length === m) { states.push(state.slice()); return; }
    for (let c = 0; c < 3; c++) {
      if (state.length === 0 || state[state.length - 1] !== c) { state.push(c); build(state); state.pop(); }
    }
  }
  build([]);
  function compatible(a, b) {
    for (let i = 0; i < m; i++) if (a[i] === b[i]) return false;
    return true;
  }
  let dp = new Array(states.length).fill(1);
  for (let col = 1; col < n; col++) {
    const next = new Array(states.length).fill(0);
    for (let j = 0; j < states.length; j++) {
      for (let k = 0; k < states.length; k++) {
        if (compatible(states[j], states[k])) next[k] = (next[k] + dp[j]) % mod;
      }
    }
    dp = next;
  }
  let total = 0;
  for (const v of dp) total = (total + v) % mod;
  return total;
}
const colorTheGrid = solve;
class Solution { colorTheGrid(m, n) { return solve(m, n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, colorTheGrid };
