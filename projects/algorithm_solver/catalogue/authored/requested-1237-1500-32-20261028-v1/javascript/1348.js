"use strict";

class TweetCounts {
  constructor() {
    this.tweets = new Map();
  }
  recordTweet(tweetName, time) {
    let arr = this.tweets.get(tweetName);
    if (!arr) { arr = []; this.tweets.set(tweetName, arr); }
    arr.push(time);
  }
  getTweetCountsPerFrequency(freq, tweetName, startTime, endTime) {
    const delta = freq === "minute" ? 60 : (freq === "hour" ? 3600 : 86400);
    const buckets = new Array(Math.floor((endTime - startTime) / delta) + 1).fill(0);
    const arr = this.tweets.get(tweetName) || [];
    for (let i = 0; i < arr.length; i++) {
      const t = arr[i];
      if (t >= startTime && t <= endTime) {
        buckets[Math.floor((t - startTime) / delta)]++;
      }
    }
    return buckets;
  }
}

function solve(operation_names, argument_lists) {
  const inst = new TweetCounts();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "recordTweet") { inst.recordTweet(args[0], args[1]); out.push(null); }
    else out.push(inst.getTweetCountsPerFrequency(args[0], args[1], args[2], args[3]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.TweetCounts = TweetCounts;
