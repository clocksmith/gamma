'use strict';
// 49. Group Anagrams.
function solve(strs) {
  const groups = new Map();
  for (const word of strs) {
    const key = [...word].sort().join('');
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(word);
  }
  return [...groups.values()];
}
const groupAnagrams = solve;
class Solution { groupAnagrams(strs) { return solve(strs); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, groupAnagrams };
