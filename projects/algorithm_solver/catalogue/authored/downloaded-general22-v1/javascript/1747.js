'use strict';

// 1747. Lexicographically Smallest String After Applying Operations (Medium).
// Specification: https://leetcode.com/problems/lexicographically-smallest-string-after-applying-operations/description/
function solve(s, a, b) {
  const n = s.length;
  const seen = new Set([s]);
  const queue = [s];
  let best = s;
  while (queue.length > 0) {
    const cur = queue.shift();
    if (cur < best) best = cur;
    const added = cur.split('').map((ch, i) => (i % 2 === 1 ? String((Number(ch) + a) % 10) : ch)).join('');
    if (!seen.has(added)) { seen.add(added); queue.push(added); }
    const rotated = b % n === 0 ? cur : cur.slice(-(b % n)) + cur.slice(0, n - (b % n));
    if (!seen.has(rotated)) { seen.add(rotated); queue.push(rotated); }
  }
  return best;
}
const findLexSmallestString = solve;
class Solution { findLexSmallestString(s, a, b) { return solve(s, a, b); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLexSmallestString };
