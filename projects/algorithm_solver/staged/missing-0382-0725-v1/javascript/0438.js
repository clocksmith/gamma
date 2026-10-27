'use strict';

// 438. Find All Anagrams in a String.

function solve(s, p) {
  const needed = new Map();
  for (const char of p) needed.set(char, (needed.get(char) || 0) + 1);
  let missing = p.length;
  const answer = [];
  for (let right = 0; right < s.length; right += 1) {
    const char = s[right], count = needed.get(char) || 0;
    if (count > 0) missing -= 1;
    needed.set(char, count - 1);
    if (right >= p.length) {
      const outgoing = s[right - p.length], next = (needed.get(outgoing) || 0) + 1;
      needed.set(outgoing, next);
      if (next > 0) missing += 1;
    }
    if (right + 1 >= p.length && missing === 0) answer.push(right - p.length + 1);
  }
  return answer;
}

const findAnagrams = solve;
class Solution {
  findAnagrams(s, p) { return solve(s, p); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findAnagrams };
