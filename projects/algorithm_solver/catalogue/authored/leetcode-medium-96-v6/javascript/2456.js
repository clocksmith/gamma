'use strict';

// 2456. Most Popular Video Creator: aggregate creator views and retain each creator's highest-view lexicographically first video.
// O(n L) expected time and O(n) auxiliary entries for maximum identifier length L; inputs are read-only.
function solve(creators, ids, views) {
  const totals = new Map();
  const bestVideo = new Map();
  for (let index = 0; index < creators.length; index += 1) {
    const creator = creators[index];
    const identifier = ids[index];
    const count = views[index];
    totals.set(creator, (totals.get(creator) || 0) + count);
    const previous = bestVideo.get(creator);
    if (!previous || count > previous[0] || (count === previous[0] && identifier < previous[1])) {
      bestVideo.set(creator, [count, identifier]);
    }
  }
  let maximum = 0;
  for (const count of totals.values()) maximum = Math.max(maximum, count);
  const result = [];
  for (const [creator, count] of totals) {
    if (count === maximum) result.push([creator, bestVideo.get(creator)[1]]);
  }
  return result;
}

const mostPopularCreator = solve;
class Solution {
  mostPopularCreator(creators, ids, views) { return solve(creators, ids, views); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mostPopularCreator };
