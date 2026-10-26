'use strict';

// 1316. Distinct Echo Substrings.
// Exact suffix ranks and LCP range minima; O(n^2 + n log^2 n) time, O(n log n) space. No probabilistic hashes.

function solve(text) {
  const n = text.length;
  if (n < 2) return 0;
  const suffixes = Array.from({ length: n }, (_, i) => i);
  let rank = Array.from(text, char => char.charCodeAt(0));
  for (let width = 1; width < n; width *= 2) {
    const second = i => i + width < n ? rank[i + width] : -1;
    suffixes.sort((a, b) => rank[a] - rank[b] || second(a) - second(b));
    const nextRank = Array(n).fill(0);
    for (let index = 1; index < n; index += 1) {
      const a = suffixes[index - 1], b = suffixes[index];
      nextRank[b] = nextRank[a] + Number(rank[a] !== rank[b] || second(a) !== second(b));
    }
    rank = nextRank;
  }
  const lcp = Array(n).fill(0);
  let length = 0;
  for (let start = 0; start < n; start += 1) {
    if (rank[start] === 0) { length = 0; continue; }
    const previous = suffixes[rank[start] - 1];
    while (start + length < n && previous + length < n && text[start + length] === text[previous + length]) length += 1;
    lcp[rank[start]] = length;
    length = Math.max(0, length - 1);
  }
  const table = [lcp];
  for (let span = 2; span <= n; span *= 2) {
    const old = table[table.length - 1];
    const half = span / 2;
    table.push(Array.from({ length: n - span + 1 }, (_, i) => Math.min(old[i], old[i + half])));
  }
  const logs = Array(n + 1).fill(0);
  for (let i = 2; i <= n; i += 1) logs[i] = logs[Math.floor(i / 2)] + 1;
  function common(a, b) {
    if (a === b) return n - a;
    const left = Math.min(rank[a], rank[b]) + 1;
    const right = Math.max(rank[a], rank[b]);
    const level = logs[right - left + 1];
    return Math.min(table[level][left], table[level][right - 2 ** level + 1]);
  }
  let answer = 0;
  for (let half = 1; half <= Math.floor(n / 2); half += 1) {
    let previous = -1;
    for (const start of suffixes) {
      if (start + 2 * half <= n && common(start, start + half) >= half) {
        if (previous === -1 || common(previous, start) < 2 * half) answer += 1;
        previous = start;
      }
    }
  }
  return answer;
}

const distinctEchoSubstrings = solve;
class Solution {
  distinctEchoSubstrings(text) { return solve(text); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctEchoSubstrings };
