"use strict";
// Hack2Hire 69557daa4a0202df9569e982 (Related Communities Finder, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(communityToFollowers, followerToCommunities, communityIdx) {
  const n = communityToFollowers.length;
  if (!(communityIdx >= 0 && communityIdx < n)) return [];
  const marked = new Array(n).fill(false);
  for (const follower of communityToFollowers[communityIdx]) {
    for (const community of followerToCommunities[Number(follower.slice(1))]) marked[Number(community.slice(1))] = true;
  }
  marked[communityIdx] = false;
  const out = [];
  for (let i = 0; i < n; i++) if (marked[i]) out.push("C" + i);
  return out;
}

function findRelatedCommunities(communityToFollowers, followerToCommunities, communityIdx) { return solve(communityToFollowers, followerToCommunities, communityIdx); }

module.exports = solve;
module.exports.findRelatedCommunities = findRelatedCommunities;
