'use strict';

// 1817. Finding the Users Active Minutes: deduplicate minutes per user and count activity totals.
// O(n + k) expected time and O(n) auxiliary space excluding the result; inputs are read-only.
function solve(logs, k) {
  const minutesByUser = new Map();
  for (const [user, minute] of logs) {
    if (!minutesByUser.has(user)) minutesByUser.set(user, new Set());
    minutesByUser.get(user).add(minute);
  }
  const answer = new Array(k).fill(0);
  for (const minutes of minutesByUser.values()) answer[minutes.size - 1] += 1;
  return answer;
}

const findingUsersActiveMinutes = solve;
class Solution {
  findingUsersActiveMinutes(logs, k) { return solve(logs, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findingUsersActiveMinutes };
