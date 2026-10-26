'use strict';

// 1282. Group the People Given the Group Size They Belong To: collect each requested size until a complete group is ready.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(groupSizes) {
  const pending = new Map();
  const result = [];
  for (let person = 0; person < groupSizes.length; person += 1) {
    const size = groupSizes[person];
    if (!pending.has(size)) pending.set(size, []);
    const group = pending.get(size);
    group.push(person);
    if (group.length === size) {
      result.push(group);
      pending.delete(size);
    }
  }
  return result;
}

const groupThePeople = solve;
class Solution {
  groupThePeople(groupSizes) { return solve(groupSizes); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, groupThePeople };
