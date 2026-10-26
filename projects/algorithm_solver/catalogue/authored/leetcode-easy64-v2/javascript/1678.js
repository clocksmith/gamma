'use strict';

// 1678. Goal Parser Interpretation (Easy).
// Specification: https://leetcode.com/problems/goal-parser-interpretation/description/
// O(n) time, O(n) space; command consists of G, (), and (al) tokens.
function solve(command) {
  const result = [];
  let index = 0;
  while (index < command.length) {
    if (command[index] === 'G') {
      result.push('G');
      index++;
    } else if (command[index + 1] === ')') {
      result.push('o');
      index += 2;
    } else {
      result.push('al');
      index += 4;
    }
  }
  return result.join('');
}

const interpret = solve;
class Solution {
  interpret(command) { return solve(command); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, interpret };
