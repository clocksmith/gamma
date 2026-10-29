"use strict";
// Hack2Hire 69557dad4a0202df9569e983 (Related Communities Finder, variant 2 of 2) over an INFERRED spec; qualification unknown.

function solve(communityToFollowers, followerToCommunities, communityIdx) {
  const n = communityToFollowers.length;
  if (!(communityIdx >= 0 && communityIdx < n)) return [];
  const seenCommunity = new Array(n).fill(false);
  const seenFollower = new Array(followerToCommunities.length).fill(false);
  seenCommunity[communityIdx] = true;
  const queue = [communityIdx];
  for (let head = 0; head < queue.length; head++) {
    for (const follower of communityToFollowers[queue[head]]) {
      const j = Number(follower.slice(1));
      if (seenFollower[j]) continue;
      seenFollower[j] = true;
      for (const other of followerToCommunities[j]) {
        const k = Number(other.slice(1));
        if (!seenCommunity[k]) { seenCommunity[k] = true; queue.push(k); }
      }
    }
  }
  seenCommunity[communityIdx] = false;
  const out = [];
  for (let i = 0; i < n; i++) if (seenCommunity[i]) out.push("C" + i);
  return out;
}

function findConnectedCommunities(communityToFollowers, followerToCommunities, communityIdx) { return solve(communityToFollowers, followerToCommunities, communityIdx); }

module.exports = solve;
module.exports.findConnectedCommunities = findConnectedCommunities;
