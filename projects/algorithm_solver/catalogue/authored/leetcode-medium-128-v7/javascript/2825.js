'use strict';

// 2825. Make String a Subsequence Using Cyclic Increments: greedily match each target character using an unchanged or once-incremented source character.
// O(n + m) time and O(1) auxiliary space; inputs are read-only.
function solve(str1, str2) {
  let matched = 0;
  for (const character of str1) {
    if (matched === str2.length) break;
    const nextCharacter = String.fromCharCode((character.charCodeAt(0) - 97 + 1) % 26 + 97);
    if (str2[matched] === character || str2[matched] === nextCharacter) matched += 1;
  }
  return matched === str2.length;
}

const canMakeSubsequence = solve;
class Solution {
  canMakeSubsequence(str1, str2) { return solve(str1, str2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canMakeSubsequence };
