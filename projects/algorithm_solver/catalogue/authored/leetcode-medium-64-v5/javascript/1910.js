'use strict';

// 1910. Remove All Occurrences of a Substring: retain prefix-match states beside the output stack for linear-time removal.
// O(len(s) + len(part)) time and auxiliary space; inputs are read-only.
function solve(s, part) {
  const failure = new Array(part.length).fill(0);
  let matched = 0;
  for (let index = 1; index < part.length; index += 1) {
    while (matched && part[index] !== part[matched]) matched = failure[matched - 1];
    if (part[index] === part[matched]) matched += 1;
    failure[index] = matched;
  }
  const output = [];
  const states = [];
  matched = 0;
  for (const letter of s) {
    while (matched && letter !== part[matched]) matched = failure[matched - 1];
    if (letter === part[matched]) matched += 1;
    output.push(letter);
    states.push(matched);
    if (matched === part.length) {
      output.length -= part.length;
      states.length -= part.length;
      matched = states.length ? states[states.length - 1] : 0;
    }
  }
  return output.join('');
}

const removeOccurrences = solve;
class Solution {
  removeOccurrences(s, part) { return solve(s, part); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeOccurrences };
