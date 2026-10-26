'use strict';

// 2707. Extra Characters in a String: combine suffix dynamic programming with trie walks for dictionary matches.
// O(W + n * L) expected time and O(W + n) auxiliary space, where W is dictionary size in characters and L is maximum word length; inputs are read-only.
function solve(s, dictionary) {
  const children = [new Map()];
  const terminal = [false];
  for (const word of dictionary) {
    let node = 0;
    for (const character of word) {
      if (!children[node].has(character)) {
        children[node].set(character, children.length);
        children.push(new Map());
        terminal.push(false);
      }
      node = children[node].get(character);
    }
    terminal[node] = true;
  }
  const best = new Int32Array(s.length + 1);
  for (let start = s.length - 1; start >= 0; start -= 1) {
    best[start] = best[start + 1] + 1;
    let node = 0;
    for (let end = start; end < s.length; end += 1) {
      const next = children[node].get(s[end]);
      if (next === undefined) break;
      node = next;
      if (terminal[node]) best[start] = Math.min(best[start], best[end + 1]);
    }
  }
  return best[0];
}

const minExtraChar = solve;
class Solution {
  minExtraChar(s, dictionary) { return solve(s, dictionary); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minExtraChar };
