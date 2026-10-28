'use strict';

// 49. Group Anagrams (Medium).
// Specification: https://leetcode.com/problems/group-anagrams/description/
function solve(strs) {
  const groups = new Map();
  for (const word of strs) {
    const key = [...word].sort().join('');
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(word);
  }
  const result = [...groups.values()].map((group) => group.slice().sort());
  result.sort((a, b) => a.join(',').localeCompare(b.join(',')));
  return result;
}
const groupAnagrams = solve;
class Solution { groupAnagrams(strs) { return solve(strs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, groupAnagrams };
