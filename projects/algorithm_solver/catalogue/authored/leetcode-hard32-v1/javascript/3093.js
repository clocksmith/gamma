'use strict';

// 3093. Longest Common Suffix Queries.
// Compact reverse trie: O(26*(S+Q)) time, O(S+query_count) space.
// First-child/sibling arrays bound lookup by the 26-letter alphabet and avoid a Map per node.
function solve(wordsContainer, wordsQuery) {
  const firstChild = [-1];
  const nextSibling = [-1];
  const symbol = [''];
  const best = [-1];
  function findChild(node, char) {
    let child = firstChild[node];
    while (child !== -1 && symbol[child] !== char) child = nextSibling[child];
    return child;
  }
  for (let index = 0; index < wordsContainer.length; index += 1) {
    const word = wordsContainer[index];
    let node = 0;
    if (best[0] === -1 || word.length < wordsContainer[best[0]].length) best[0] = index;
    for (let offset = word.length - 1; offset >= 0; offset -= 1) {
      const char = word[offset];
      let child = findChild(node, char);
      if (child === -1) {
        child = firstChild.length;
        firstChild.push(-1);
        nextSibling.push(firstChild[node]);
        symbol.push(char);
        best.push(index);
        firstChild[node] = child;
      }
      node = child;
      if (word.length < wordsContainer[best[node]].length) best[node] = index;
    }
  }
  const answer = [];
  for (const word of wordsQuery) {
    let node = 0;
    for (let offset = word.length - 1; offset >= 0; offset -= 1) {
      const child = findChild(node, word[offset]);
      if (child === -1) break;
      node = child;
    }
    answer.push(best[node]);
  }
  return answer;
}

const stringIndices = solve;
class Solution {
  stringIndices(wordsContainer, wordsQuery) { return solve(wordsContainer, wordsQuery); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, stringIndices };
