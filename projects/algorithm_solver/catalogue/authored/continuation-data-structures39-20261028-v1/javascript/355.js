"use strict";

class Twitter {
  constructor() {
    this.time = 0;
    this.tweets = new Map();
    this.following = new Map();
  }
  postTweet(userId, tweetId) {
    this.time += 1;
    let bucket = this.tweets.get(userId);
    if (!bucket) {
      bucket = [];
      this.tweets.set(userId, bucket);
    }
    bucket.push([this.time, tweetId]);
    if (bucket.length > 10) bucket.shift();
  }
  getNewsFeed(userId) {
    const users = new Set(this.following.get(userId) || []);
    users.add(userId);
    const heap = [];
    const pushHeap = (item) => {
      heap.push(item);
      let i = heap.length - 1;
      while (i > 0) {
        const p = (i - 1) >> 1;
        if (heap[p][0] >= heap[i][0]) break;
        const t = heap[p]; heap[p] = heap[i]; heap[i] = t;
        i = p;
      }
    };
    const popHeap = () => {
      const top = heap[0];
      const last = heap.pop();
      if (heap.length > 0) {
        heap[0] = last;
        let i = 0;
        const n = heap.length;
        while (true) {
          let l = (i << 1) + 1, r = l + 1, b = i;
          if (l < n && heap[l][0] > heap[b][0]) b = l;
          if (r < n && heap[r][0] > heap[b][0]) b = r;
          if (b === i) break;
          const t = heap[i]; heap[i] = heap[b]; heap[b] = t;
          i = b;
        }
      }
      return top;
    };
    for (const u of users) {
      const tlist = this.tweets.get(u);
      if (tlist && tlist.length > 0) {
        const idx = tlist.length - 1;
        pushHeap([tlist[idx][0], tlist[idx][1], tlist, idx - 1]);
      }
    }
    const res = [];
    while (heap.length > 0 && res.length < 10) {
      const [ts, tid, tlist, prevIdx] = popHeap();
      res.push(tid);
      if (prevIdx >= 0) {
        pushHeap([tlist[prevIdx][0], tlist[prevIdx][1], tlist, prevIdx - 1]);
      }
    }
    return res;
  }
  follow(followerId, followeeId) {
    if (followerId === followeeId) return;
    let s = this.following.get(followerId);
    if (!s) {
      s = new Set();
      this.following.set(followerId, s);
    }
    s.add(followeeId);
  }
  unfollow(followerId, followeeId) {
    const s = this.following.get(followerId);
    if (s) s.delete(followeeId);
  }
}

function solve(operation_names, argument_lists) {
  const instance = new Twitter();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "postTweet") {
      instance.postTweet(args[0], args[1]);
      out.push(null);
    } else if (op === "getNewsFeed") {
      out.push(instance.getNewsFeed(args[0]));
    } else if (op === "follow") {
      instance.follow(args[0], args[1]);
      out.push(null);
    } else if (op === "unfollow") {
      instance.unfollow(args[0], args[1]);
      out.push(null);
    } else {
      throw new Error("unknown operation");
    }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Twitter = Twitter;
