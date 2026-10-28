'use strict';

// 2468. Split Message Based on Limit (Hard).
// Specification: https://leetcode.com/problems/split-message-based-on-limit/description/
function solve(message, limit) {
  const n = message.length;
  let sa = 0;
  for (let k = 1; k <= n; k++) {
    sa += String(k).length;
    const sb = String(k).length * k;
    const sc = 3 * k;
    if (String(k).length * 2 + 3 >= limit) continue;
    if (limit * k - (sa + sb + sc) >= n) {
      const out = []; let idx = 0;
      for (let part = 1; part <= k; part++) {
        const tag = '<' + part + '/' + k + '>';
        const cap = limit - tag.length;
        const chunk = message.slice(idx, idx + cap);
        idx += chunk.length;
        out.push(chunk + tag);
      }
      return out;
    }
  }
  return [];
}
const splitMessage = solve;
class Solution { splitMessage(message, limit) { return solve(message, limit); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, splitMessage };
