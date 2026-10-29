"use strict";
// Hack2Hire 68e2d042dab409e303d92952 (Friends by Last-K Movie Overlap, variant 2 of 2) over an INFERRED spec; qualification unknown.

function lowerBound(list, value) {
  let lo = 0, hi = list.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (list[mid] < value) lo = mid + 1; else hi = mid; }
  return lo;
}

class MovieFriends {
  constructor(k) {
    this.k = k;
    this.state = new Map();   // customer -> {window, counts, distinct}
    this.key = new Map();     // customer -> current key (only once the window is full)
    this.buckets = new Map(); // key -> sorted customers
  }

  watch(customerId, movieId) {
    let s = this.state.get(customerId);
    if (s === undefined) { s = { window: [], counts: new Map(), distinct: [] }; this.state.set(customerId, s); }
    s.window.push(movieId);
    const c = (s.counts.get(movieId) || 0) + 1;
    s.counts.set(movieId, c);
    if (c === 1) s.distinct.splice(lowerBound(s.distinct, movieId), 0, movieId);
    if (s.window.length > this.k) {
      const old = s.window.shift(); // k <= 50, so shifting is cheap
      const left = s.counts.get(old) - 1;
      if (left === 0) { s.counts.delete(old); s.distinct.splice(lowerBound(s.distinct, old), 1); }
      else s.counts.set(old, left);
    }
    if (s.window.length === this.k) {
      const next = s.distinct.join(","), oldKey = this.key.get(customerId);
      if (next !== oldKey) {
        if (oldKey !== undefined) {
          const bucket = this.buckets.get(oldKey);
          bucket.splice(lowerBound(bucket, customerId), 1);
          if (!bucket.length) this.buckets.delete(oldKey);
        }
        if (!this.buckets.has(next)) this.buckets.set(next, []);
        const bucket = this.buckets.get(next);
        bucket.splice(lowerBound(bucket, customerId), 0, customerId);
        this.key.set(customerId, next);
      }
    }
  }

  getFriends(customerId) {
    const key = this.key.get(customerId);
    if (key === undefined) return [];
    return this.buckets.get(key).filter((c) => c !== customerId);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "MovieFriends" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new MovieFriends(...argumentLists[0]);
  const allowed = new Set(["watch", "getFriends"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.MovieFriends = MovieFriends;
