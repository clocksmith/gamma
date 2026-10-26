'use strict';

// 2217. Find Palindrome With Fixed Length: index the nonzero-leading first half and mirror it without repeating an odd center.
// O(q * L) time and O(q + L) space for q queries and digit length L <= 15; inputs are read-only.
function solve(queries, intLength) {
  const halfLength = Math.floor((intLength + 1) / 2);
  const first = 10 ** (halfLength - 1);
  const limit = 10 ** halfLength;
  const answer = [];
  for (const query of queries) {
    const half = first + query - 1;
    if (half >= limit) { answer.push(-1); continue; }
    const prefix = String(half);
    const reflected = intLength % 2 ? prefix.slice(0, -1) : prefix;
    // At most 15 decimal digits, so the result remains an exact Number.
    answer.push(Number(prefix + reflected.split('').reverse().join('')));
  }
  return answer;
}

const kthPalindrome = solve;
class Solution {
  kthPalindrome(queries, intLength) { return solve(queries, intLength); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthPalindrome };
