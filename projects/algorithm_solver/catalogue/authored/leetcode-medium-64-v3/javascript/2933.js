'use strict';

// 2933. High-Access Employees: find three sorted same-day accesses less than sixty minutes apart.
// O(n log n) time and O(n) auxiliary space for bounded-length employee names; inputs are read-only.
function solve(access_times) {
  const times = new Map();
  for (const [name, clock] of access_times) {
    const minute = Number(clock.slice(0, 2)) * 60 + Number(clock.slice(2));
    if (!times.has(name)) times.set(name, []);
    times.get(name).push(minute);
  }
  const result = [];
  for (const [name, visits] of times) {
    visits.sort((left, right) => left - right);
    for (let index = 2; index < visits.length; index += 1) {
      if (visits[index] - visits[index - 2] < 60) {
        result.push(name);
        break;
      }
    }
  }
  return result.sort();
}

const findHighAccessEmployees = solve;
class Solution {
  findHighAccessEmployees(access_times) { return solve(access_times); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findHighAccessEmployees };
