"use strict";
// Hack2Hire 68094bed31dc778b35c5d171 (Violation Log Analyzer) over an INFERRED spec; qualification unknown.

function lowerBound(arr, value) {
  let lo = 0, hi = arr.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid] < value) lo = mid + 1; else hi = mid; }
  return lo;
}

function upperBound(arr, value) {
  let lo = 0, hi = arr.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (arr[mid] <= value) lo = mid + 1; else hi = mid; }
  return lo;
}

function distinct(dates, keys, start, end) {
  if (start > end) return 0;
  const hi = upperBound(dates, end), seen = new Set();
  for (let k = lowerBound(dates, start); k < hi; k++) seen.add(keys[k]);
  return seen.size;
}

class ViolationLogAnalyzer {
  constructor(logs) {
    this.dates = logs.map((log) => log[2]);
    this.pairs = logs.map((log) => log[0] + "|" + log[1]);
    this.byPost = new Map();
    this.byPolicy = new Map();
    for (const [post, policy, date] of logs) {
      if (!this.byPost.has(post)) this.byPost.set(post, [[], []]);
      const a = this.byPost.get(post); a[0].push(date); a[1].push(policy);
      if (!this.byPolicy.has(policy)) this.byPolicy.set(policy, [[], []]);
      const b = this.byPolicy.get(policy); b[0].push(date); b[1].push(post);
    }
  }

  countPolicies(postId, startDate, endDate) {
    const g = this.byPost.get(postId);
    return g === undefined ? 0 : distinct(g[0], g[1], startDate, endDate);
  }

  countPosts(policy, startDate, endDate) {
    const g = this.byPolicy.get(policy);
    return g === undefined ? 0 : distinct(g[0], g[1], startDate, endDate);
  }

  countViolations(startDate, endDate) {
    return distinct(this.dates, this.pairs, startDate, endDate);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ViolationLogAnalyzer" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new ViolationLogAnalyzer(...argumentLists[0]);
  const allowed = new Set(["countPolicies", "countPosts", "countViolations"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ViolationLogAnalyzer = ViolationLogAnalyzer;
