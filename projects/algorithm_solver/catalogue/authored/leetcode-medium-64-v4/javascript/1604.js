'use strict';

// 1604. Alert Using Same Key-Card Three or More Times in a One Hour Period: sort each person's same-day uses and inspect consecutive triples.
// O(n log(n + 1)) time and O(n) auxiliary space on the bounded name domain; inputs are read-only.
function solve(keyName, keyTime) {
  const uses = new Map();
  for (let index = 0; index < keyName.length; index += 1) {
    const name = keyName[index];
    const time = keyTime[index];
    const minute = Number(time.slice(0, 2)) * 60 + Number(time.slice(3));
    if (!uses.has(name)) uses.set(name, []);
    uses.get(name).push(minute);
  }
  const result = [];
  for (const [name, times] of uses) {
    times.sort((a, b) => a - b);
    for (let index = 2; index < times.length; index += 1) {
      if (times[index] - times[index - 2] <= 60) {
        result.push(name);
        break;
      }
    }
  }
  return result.sort();
}

const alertNames = solve;
class Solution {
  alertNames(keyName, keyTime) { return solve(keyName, keyTime); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, alertNames };
