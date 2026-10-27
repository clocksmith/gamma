/**
 * 3777. Minimum Deletions to Make Alternating Substring
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-deletions-to-make-alternating-substring/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3777.Minimum%20Deletions%20to%20Make%20Alternating%20Substring/README_EN.md
 * Complexity: O((n+q) log n) time; O(n+q) space.
 * Canonical solve(s,queries); native stub pending. Flips update private string state; deletion queries do not delete characters.
 */

function solve(s, queries) {
  const characters = s.split(''), n = s.length, tree = Array(n + 1).fill(0);
  function add(index, change) { while (index <= n) { tree[index] += change; index += index & -index; } }
  function prefix(index) { let result = 0; while (index > 0) { result += tree[index]; index -= index & -index; } return result; }
  for (let right = 1; right < n; right += 1) add(right, characters[right - 1] === characters[right] ? 1 : 0);
  const answers = [];
  for (const query of queries) {
    if (query[0] === 2) { answers.push(prefix(query[2]) - prefix(query[1])); continue; }
    const position = query[1];
    for (const right of [position, position + 1]) if (right > 0 && right < n) add(right, characters[right - 1] === characters[right] ? -1 : 0);
    characters[position] = characters[position] === 'A' ? 'B' : 'A';
    for (const right of [position, position + 1]) if (right > 0 && right < n) add(right, characters[right - 1] === characters[right] ? 1 : 0);
  }
  return answers;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
