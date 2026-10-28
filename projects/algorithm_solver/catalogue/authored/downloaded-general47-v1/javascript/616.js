'use strict';

// 616. Add Bold Tag in String (Medium).
// Specification: https://leetcode.com/problems/add-bold-tag-in-string/description/
function solve(s, words) {
  const bold = new Array(s.length).fill(false);
  for (const word of words) {
    let start = s.indexOf(word);
    while (start !== -1) {
      for (let i = start; i < start + word.length; i++) bold[i] = true;
      start = s.indexOf(word, start + 1);
    }
  }
  let result = '';
  for (let i = 0; i < s.length; i++) {
    if (bold[i] && (i === 0 || !bold[i - 1])) result += '<b>';
    result += s[i];
    if (bold[i] && (i + 1 === s.length || !bold[i + 1])) result += '</b>';
  }
  return result;
}
const addBoldTag = solve;
class Solution { addBoldTag(s, words) { return solve(s, words); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, addBoldTag };
