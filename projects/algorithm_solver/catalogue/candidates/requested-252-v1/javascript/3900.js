'use strict';

// 3900. Longest Balanced Substring After One Swap.
// Specification: https://leetcode.com/problems/longest-balanced-substring-after-one-swap/description/
// O(n) expected time and O(n) space with lazily advanced prefix-position lists. A repairable even-length substring has imbalance 0 or +/-2 and cannot exceed twice the total minority count.
function solve(s) {
  let ones = 0;
  for (const character of s) if (character === '1') ones++;
  const limit = 2 * Math.min(ones, s.length - ones);
  if (limit === 0) return 0;
  const positions = new Map([[0, { indices: [0], head: 0 }]]);
  let balance = 0, answer = 0;
  for (let end = 1; end <= s.length; end++) {
    balance += s[end - 1] === '1' ? 1 : -1;
    for (const target of [balance - 2, balance, balance + 2]) {
      const entry = positions.get(target);
      if (!entry) continue;
      while (entry.head < entry.indices.length && entry.indices[entry.head] < end - limit) entry.head++;
      if (entry.head < entry.indices.length) answer = Math.max(answer, end - entry.indices[entry.head]);
    }
    if (!positions.has(balance)) positions.set(balance, { indices: [], head: 0 });
    positions.get(balance).indices.push(end);
  }
  return answer;
}

// Native judge method name is not established; canonical solve is the supported entry point.
if (typeof module !== 'undefined') module.exports = { solve };
