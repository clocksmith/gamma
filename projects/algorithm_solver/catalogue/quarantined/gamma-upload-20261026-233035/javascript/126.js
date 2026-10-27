'use strict';
// 126. Word Ladder II.
function solve(beginWord, endWord, wordList) {
  const words = new Set(wordList);
  if (!words.has(endWord)) return [];
  const parents = new Map();
  const distance = new Map([[beginWord, 0]]);
  const queue = [beginWord];
  for (let head = 0; head < queue.length; head += 1) {
    const word = queue[head];
    const step = distance.get(word) + 1;
    for (let index = 0; index < word.length; index += 1) {
      for (let code = 97; code <= 122; code += 1) {
        const candidate = word.slice(0, index) + String.fromCharCode(code) + word.slice(index + 1);
        if (!words.has(candidate)) continue;
        if (!distance.has(candidate)) { distance.set(candidate, step); queue.push(candidate); }
        if (distance.get(candidate) === step) {
          if (!parents.has(candidate)) parents.set(candidate, []);
          parents.get(candidate).push(word);
        }
      }
    }
  }
  if (!distance.has(endWord)) return [];
  const result = [];
  const path = [endWord];
  function build(word) {
    if (word === beginWord) { result.push(path.slice().reverse()); return; }
    for (const parent of parents.get(word) || []) { path.push(parent); build(parent); path.pop(); }
  }
  build(endWord);
  return result;
}
const findLadders = solve;
class Solution { findLadders(beginWord, endWord, wordList) { return solve(beginWord, endWord, wordList); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLadders };
