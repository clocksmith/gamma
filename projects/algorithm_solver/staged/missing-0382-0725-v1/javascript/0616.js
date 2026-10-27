'use strict';

// 616. Add Bold Tag in String. Merge overlapping and adjacent matching intervals before emitting tags.

function solve(s, words) {
  const difference = Array(s.length + 1).fill(0);
  for (const word of words) {
    if (word.length === 0) continue;
    for (let start = s.indexOf(word); start !== -1; start = s.indexOf(word, start + 1)) {
      difference[start] += 1; difference[start + word.length] -= 1;
    }
  }
  const parts = [];
  let active = 0;
  for (let i = 0; i < s.length; i += 1) {
    const before = active;
    active += difference[i];
    if (before === 0 && active > 0) parts.push('<b>');
    else if (before > 0 && active === 0) parts.push('</b>');
    parts.push(s[i]);
  }
  if (active > 0) parts.push('</b>');
  return parts.join('');
}

const addBoldTag = solve;
class Solution {
  addBoldTag(s, words) { return solve(s, words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addBoldTag };
