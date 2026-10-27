'use strict';

// 527. Word Abbreviation. Neighbor longest-common-prefix lengths resolve collisions within equal length/first/last groups.

function solve(words) {
  const groups = new Map(), answer = words.slice();
  words.forEach((word, i) => {
    const key = `${word.length}:${word[0]}:${word[word.length - 1]}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(i);
  });
  function common(a, b) {
    let length = 0;
    while (length < Math.min(a.length, b.length) && a[length] === b[length]) length += 1;
    return length;
  }
  for (const indices of groups.values()) {
    indices.sort((a, b) => words[a] < words[b] ? -1 : words[a] > words[b] ? 1 : 0);
    for (let position = 0; position < indices.length; position += 1) {
      const index = indices[position], word = words[index];
      let shared = 0;
      if (position > 0) shared = Math.max(shared, common(word, words[indices[position - 1]]));
      if (position + 1 < indices.length) shared = Math.max(shared, common(word, words[indices[position + 1]]));
      const prefix = Math.max(1, shared + 1), skipped = word.length - prefix - 1;
      if (skipped > 0) {
        const abbreviation = word.slice(0, prefix) + String(skipped) + word[word.length - 1];
        if (abbreviation.length < word.length) answer[index] = abbreviation;
      }
    }
  }
  return answer;
}

const wordsAbbreviation = solve;
class Solution {
  wordsAbbreviation(words) { return solve(words); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, wordsAbbreviation };
