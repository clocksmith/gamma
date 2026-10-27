'use strict';
// 355. Design Twitter.
class Twitter {
  constructor() { this.time = 0; this.posts = new Map(); this.following = new Map(); }
  postTweet(userId, tweetId) {
    if (!this.posts.has(userId)) this.posts.set(userId, []);
    this.posts.get(userId).push([++this.time, tweetId]);
  }
  getNewsFeed(userId) {
    const users = new Set([userId, ...(this.following.get(userId) || [])]);
    const posts = [];
    for (const user of users) posts.push(...(this.posts.get(user) || []).slice(-10));
    return posts.sort((a, b) => b[0] - a[0]).slice(0, 10).map(row => row[1]);
  }
  follow(followerId, followeeId) {
    if (!this.following.has(followerId)) this.following.set(followerId, new Set());
    this.following.get(followerId).add(followeeId);
  }
  unfollow(followerId, followeeId) { if (this.following.has(followerId)) this.following.get(followerId).delete(followeeId); }
}
function solve(operations, args) {
  const twitter = new Twitter();
  return operations.map((operation, index) => operation === 'Twitter' ? null : twitter[operation](...args[index]));
}
if (typeof module !== 'undefined') module.exports = { solve, Twitter };
