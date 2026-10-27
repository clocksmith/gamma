'use strict';
// 277. Find the Celebrity.
function solve(n, knowsFn = globalThis.knows) {
  let candidate = 0;
  for (let person = 1; person < n; person += 1) if (knowsFn(candidate, person)) candidate = person;
  for (let person = 0; person < n; person += 1) {
    if (person !== candidate && (knowsFn(candidate, person) || !knowsFn(person, candidate))) return -1;
  }
  return candidate;
}
class Solution { findCelebrity(n) { return solve(n); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution };
