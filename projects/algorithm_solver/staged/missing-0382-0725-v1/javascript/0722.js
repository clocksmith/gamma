'use strict';

// 722. Remove Comments. Carry a partial output line across block comments, discarding only empty resulting lines.

function solve(source) {
  const answer = [];
  let buffer = [], inside = false;
  for (const line of source) {
    let i = 0;
    while (i < line.length) {
      const pair = line.slice(i, i + 2);
      if (inside) {
        if (pair === '*/') { inside = false; i += 2; } else i += 1;
      } else if (pair === '//') break;
      else if (pair === '/*') { inside = true; i += 2; }
      else buffer.push(line[i++]);
    }
    if (!inside && buffer.length > 0) { answer.push(buffer.join('')); buffer = []; }
  }
  return answer;
}

const removeComments = solve;
class Solution {
  removeComments(source) { return solve(source); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeComments };
