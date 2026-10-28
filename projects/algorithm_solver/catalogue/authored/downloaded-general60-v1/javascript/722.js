'use strict';

// 722. Remove Comments (Medium).
// Specification: https://leetcode.com/problems/remove-comments/description/
function solve(source) {
  const result = [];
  let inBlock = false;
  let current = '';
  for (const line of source) {
    let i = 0;
    while (i < line.length) {
      if (!inBlock && i + 1 < line.length && line[i] === '/' && line[i + 1] === '*') { inBlock = true; i += 2; }
      else if (inBlock && i + 1 < line.length && line[i] === '*' && line[i + 1] === '/') { inBlock = false; i += 2; }
      else if (!inBlock && i + 1 < line.length && line[i] === '/' && line[i + 1] === '/') break;
      else if (!inBlock) { current += line[i]; i++; }
      else i++;
    }
    if (!inBlock && current !== '') { result.push(current); current = ''; }
  }
  return result;
}
const removeComments = solve;
class Solution { removeComments(source) { return solve(source); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeComments };
