'use strict';

// 1311. Get Watched Videos by Your Friends (Medium).
// Specification: https://leetcode.com/problems/get-watched-videos-by-your-friends/description/
function solve(watchedVideos, friends, id, level) {
  const seen = new Set([id]);
  let frontier = [id];
  for (let step = 0; step < level; step++) {
    const next = [];
    for (const person of frontier) {
      for (const friend of friends[person]) {
        if (!seen.has(friend)) { seen.add(friend); next.push(friend); }
      }
    }
    frontier = next;
  }
  const counts = new Map();
  for (const person of frontier) {
    for (const video of watchedVideos[person]) {
      counts.set(video, (counts.get(video) || 0) + 1);
    }
  }
  return [...counts.entries()].sort((a, b) => (a[1] - b[1]) || (a[0] < b[0] ? -1 : 1)).map((entry) => entry[0]);
}
const watchedVideosByFriends = solve;
class Solution { watchedVideosByFriends(...args) { return solve(...args); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, watchedVideosByFriends };
