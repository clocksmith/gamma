'use strict';

// 2306. Naming a Company. Count nonshared suffixes between initial-letter groups; O(L+26*n) time and O(L+n) space. Inputs are preserved.

function solve(ideas) {
  const groups = Array.from({ length: 26 }, () => new Set());
  for (const word of ideas) groups[word.charCodeAt(0) - 97].add(word.slice(1));
  let answer = 0;
  for (let first = 0; first < 26; first += 1) {
    for (let second = first + 1; second < 26; second += 1) {
      let smaller = groups[first];
      let larger = groups[second];
      if (smaller.size > larger.size) [smaller, larger] = [larger, smaller];
      let common = 0;
      for (const suffix of smaller) if (larger.has(suffix)) common += 1;
      answer += 2 * (groups[first].size - common) * (groups[second].size - common);
    }
  }
  return answer;
}

const distinctNames = solve;
class Solution {
  distinctNames(ideas) { return solve(ideas); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distinctNames };
