'use strict';

// 2564. Substring XOR Queries (Medium).
// Specification: https://leetcode.com/problems/substring-xor-queries/description/
function solve(s, queries) {
  const best = new Map();
  const n = s.length;
  const LIMIT = 1 << 30;
  for (let i = 0; i < n; i++) {
    let val = 0;
    for (let j = i; j < Math.min(n, i + 30); j++) {
      val = val * 2 + (s.charCodeAt(j) - 48);
      if (val >= LIMIT) break;
      const len = j - i + 1;
      const cur = best.get(val);
      if (!cur || len < cur[2] || (len === cur[2] && i < cur[0])) best.set(val, [i, j, len]);
      if (s[i] === '0') break;
    }
  }
  return queries.map(([first, second]) => {
    const hit = best.get(first ^ second);
    return hit ? [hit[0], hit[1]] : [-1, -1];
  });
}
const substringXorQueries = solve;
class Solution { substringXorQueries(s, queries) { return solve(s, queries); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, substringXorQueries };
