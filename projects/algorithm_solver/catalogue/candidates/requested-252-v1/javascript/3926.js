/**
 * 3926. Count Valid Word Occurrences
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-valid-word-occurrences/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3926.Count%20Valid%20Word%20Occurrences/README_EN.md
 * Complexity: O(total text + total query characters) time and space.
 * ASCII lowercase words; hyphen joins only when directly between letters; chunks concatenate without separators.
 */

function solve(chunks, queries) {
  const counts = new Map();
  const text = chunks.join('');
  for (const match of text.matchAll(/[a-z]+(?:-[a-z]+)*/g)) {
    const word = match[0];
    counts.set(word, (counts.get(word) || 0) + 1);
  }
  return queries.map(word => counts.get(word) || 0);
}

function countWordOccurrences(chunks, queries) {
  return solve(chunks, queries);
}

class Solution {
  countWordOccurrences(chunks, queries) {
    return solve(chunks, queries);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countWordOccurrences, Solution };
}
