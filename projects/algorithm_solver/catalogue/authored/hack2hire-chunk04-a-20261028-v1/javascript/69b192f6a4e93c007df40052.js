"use strict";
// Hack2Hire 69b192f6a4e93c007df40052 (Snapshot Social Graph, level 2) over an INFERRED spec; qualification unknown.

function upperBound(values, x) {
  let lo = 0, hi = values.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (values[mid] <= x) lo = mid + 1; else hi = mid; }
  return lo;
}

class SocialNetwork {
  constructor() { this.current = 0; this.history = new Map(); this.touched = new Map(); }

  _record(follower, followee, state) {
    const key = follower + ',' + followee;
    let entry = this.history.get(key);
    if (entry === undefined) {
      if (!state) return;
      entry = [[], []];
      this.history.set(key, entry);
      if (!this.touched.has(follower)) this.touched.set(follower, []);
      this.touched.get(follower).push(followee);
    }
    const [snaps, states] = entry;
    if (snaps.length && snaps[snaps.length - 1] === this.current) states[states.length - 1] = state;
    else { snaps.push(this.current); states.push(state); }
  }

  _at(follower, followee, snapshotId) {
    const entry = this.history.get(follower + ',' + followee);
    if (entry === undefined) return false;
    const i = upperBound(entry[0], snapshotId) - 1;
    return i >= 0 && entry[1][i];
  }

  follow(followerId, followeeId) { this._record(followerId, followeeId, true); }

  unfollow(followerId, followeeId) { this._record(followerId, followeeId, false); }

  snapshot() { this.current += 1; return this.current - 1; }

  isFollowing(followerId, followeeId, snapshotId) { return this._at(followerId, followeeId, snapshotId); }

  getFollowees(userId, snapshotId) {
    const out = (this.touched.get(userId) || []).filter((e) => this._at(userId, e, snapshotId));
    return out.sort((x, y) => x - y);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SocialNetwork" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new SocialNetwork(...argumentLists[0]);
  const allowed = new Set(["follow", "unfollow", "snapshot", "isFollowing", "getFollowees"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.SocialNetwork = SocialNetwork;
