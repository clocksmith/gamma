'use strict';

// 472. Concatenated Words: shorter-word trie and segmentation dynamic programming.
// O(sum(length^2)) time and O(total characters) auxiliary space. Inputs are preserved.
function solve(words) {
  const children = [new Map()];
  const terminal = [false];
  const concatenated = new Set();
  const ordered = words.slice().sort((a, b) => a.length - b.length);
  for (const word of ordered) {
    if (word.length === 0) continue;
    const pieces = new Int32Array(word.length + 1).fill(-1);
    pieces[0] = 0;
    for (let start = 0; start < word.length; start += 1) {
      if (pieces[start] < 0) continue;
      let node = 0;
      for (let end = start; end < word.length; end += 1) {
        const next = children[node].get(word[end]);
        if (next === undefined) break;
        node = next;
        if (terminal[node]) pieces[end + 1] = Math.max(pieces[end + 1], pieces[start] + 1);
      }
    }
    if (pieces[word.length] >= 2) concatenated.add(word);
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
  return words.filter(word => concatenated.has(word));
}

const findAllConcatenatedWordsInADict = solve;
class Solution {
  findAllConcatenatedWordsInADict(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findAllConcatenatedWordsInADict };
