'use strict';

// 614. Second Degree Follower. Gamma row-record adapter for the SQL problem, not a native SQL submission. Each table is a list of dictionaries with the statement column names; the result is a list of dictionaries. SQL NULL is None/null. Inputs are preserved. follow: followee, follower; pairs are unique. Output: follower, num, ordered by follower.

function solve(follow) {
  const following = new Set(follow.map(row => row.follower));
  const counts = new Map();
  for (const row of follow) counts.set(row.followee, (counts.get(row.followee) || 0) + 1);
  return [...counts.keys()].sort().filter(user => following.has(user)).map(user => ({follower: user, num: counts.get(user)}));
}

const secondDegreeFollower = solve;
class Solution {
  secondDegreeFollower(follow) { return solve(follow); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, secondDegreeFollower };
