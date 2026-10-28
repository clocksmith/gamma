'use strict';

// 127. Word Ladder (Hard).
// Specification: https://leetcode.com/problems/word-ladder/description/
function solve(beginWord, endWord, wordList) {
  const words = new Set(wordList);
  if (!words.has(endWord)) return 0;
  let queue = [beginWord];
  let steps = 1;
  const visited = new Set([beginWord]);
  while (queue.length > 0) {
    const nextQueue = [];
    for (const word of queue) {
      if (word === endWord) return steps;
      for (let i = 0; i < word.length; i++) {
        for (let code = 97; code <= 122; code++) {
          const candidate = word.slice(0, i) + String.fromCharCode(code) + word.slice(i + 1);
          if (words.has(candidate) && !visited.has(candidate)) { visited.add(candidate); nextQueue.push(candidate); }
        }
      }
    }
    queue = nextQueue;
    steps++;
  }
  return 0;
}
const ladderLength = solve;
class Solution { ladderLength(beginWord, endWord, wordList) { return solve(beginWord, endWord, wordList); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, ladderLength };
