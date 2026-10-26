'use strict';

// 1733. Minimum Number of People to Teach: teach one language only to endpoints of friendships lacking a shared language.
// O(L + f * n) expected time and O(L + m + n) space, with L known-language entries, m users and f friendships; inputs are read-only.
function solve(n, languages, friendships) {
  const known = languages.map(values => new Set(values));
  const affected = new Set();
  for (const [left, right] of friendships) {
    let common = false;
    for (const language of known[left - 1]) {
      if (known[right - 1].has(language)) {
        common = true;
        break;
      }
    }
    if (!common) {
      affected.add(left - 1);
      affected.add(right - 1);
    }
  }
  const counts = new Array(n + 1).fill(0);
  let mostKnown = 0;
  for (const person of affected) {
    for (const language of known[person]) {
      counts[language] += 1;
      mostKnown = Math.max(mostKnown, counts[language]);
    }
  }
  return affected.size - mostKnown;
}

const minimumTeachings = solve;
class Solution {
  minimumTeachings(n, languages, friendships) { return solve(n, languages, friendships); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTeachings };
