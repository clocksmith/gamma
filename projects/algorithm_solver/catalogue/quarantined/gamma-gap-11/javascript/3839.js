'use strict';

// 3839. Number of Prefix Connected Groups.
// O(n k) expected time and O(n k) space; each repeated prefix contributes one group.
function solve(words, k) {
  const counts = new Map();
  for (const word of words) {
    if (word.length < k) continue;
    const prefix = word.slice(0, k);
    counts.set(prefix, (counts.get(prefix) || 0) + 1);
  }
  let answer = 0;
  for (const count of counts.values()) if (count >= 2) answer += 1;
  return answer;
}

const prefixConnected = solve;
class Solution {
  prefixConnected(words, k) { return solve(words, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, prefixConnected };
