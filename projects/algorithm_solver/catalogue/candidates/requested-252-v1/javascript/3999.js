/**
 * 3999. Minimum Number of String Groups Through Transformations
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/minimum-number-of-string-groups-through-transformations/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3999.Minimum%20Number%20of%20String%20Groups%20Through%20Transformations/README_EN.md
 * Complexity: O(total characters) expected time and space.
 * Independent cyclic rotations, not arbitrary permutations. Booth canonicalizes each parity subsequence exactly; pair keys preserve length and order without hash-only equality. Native method unconfirmed.
 */

function solve(words) {
  function rotation(s) {
    const n = s.length;
    if (n <= 1) return s;
    const doubled = s + s;
    let a = 0, b = 1, offset = 0;
    while (a < n && b < n && offset < n) {
      const x = doubled[a + offset], y = doubled[b + offset];
      if (x === y) { offset++; continue; }
      if (x > y) { a += offset + 1; if (a === b) a++; }
      else { b += offset + 1; if (b === a) b++; }
      offset = 0;
    }
    const start = Math.min(a, b);
    return doubled.slice(start, start + n);
  }
  const groups = new Set();
  for (const word of words) {
    const even = [], odd = [];
    for (let i = 0; i < word.length; i++) (i % 2 ? odd : even).push(word[i]);
    groups.add(rotation(even.join('')) + '|' + rotation(odd.join('')));
  }
  return groups.size;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
