'use strict';

// 1531. String Compression II: memoized suffix/deletion DP over retained runs; O(n^2*(k+1)) time and O(n*(k+1)) space.

function solve(s, k) {
  const memo = Array.from({ length: s.length }, () => Array(k + 1).fill(-1));
  function best(start, remaining) {
    if (remaining < 0) return s.length + 1;
    if (s.length - start <= remaining) return 0;
    if (memo[start][remaining] !== -1) return memo[start][remaining];
    let answer = best(start + 1, remaining - 1);
    let kept = 0;
    let removed = 0;
    for (let end = start; end < s.length; end += 1) {
      if (s[end] === s[start]) kept += 1;
      else removed += 1;
      if (removed > remaining) break;
      const encoded = kept === 1 ? 1 : 1 + String(kept).length;
      answer = Math.min(answer, encoded + best(end + 1, remaining - removed));
    }
    memo[start][remaining] = answer;
    return answer;
  }
  return best(0, k);
}

const getLengthOfOptimalCompression = solve;
class Solution {
  getLengthOfOptimalCompression(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getLengthOfOptimalCompression };
