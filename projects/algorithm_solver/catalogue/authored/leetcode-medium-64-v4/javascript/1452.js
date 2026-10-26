'use strict';

// 1452. People Whose List of Favorite Companies Is Not a Subset of Another List: compare company sets without changing their original lists.
// O(n * S) expected time and O(S) auxiliary space, where S is total company membership; inputs are read-only.
function solve(favoriteCompanies) {
  const companies = favoriteCompanies.map(names => new Set(names));
  const result = [];
  for (let index = 0; index < companies.length; index += 1) {
    const names = companies[index];
    let contained = false;
    for (let other = 0; other < companies.length && !contained; other += 1) {
      if (other === index || companies[other].size < names.size) continue;
      let subset = true;
      for (const name of names) {
        if (!companies[other].has(name)) {
          subset = false;
          break;
        }
      }
      contained = subset;
    }
    if (!contained) result.push(index);
  }
  return result;
}

const peopleIndexes = solve;
class Solution {
  peopleIndexes(favoriteCompanies) { return solve(favoriteCompanies); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, peopleIndexes };
