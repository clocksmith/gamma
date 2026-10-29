// Original hack2hire:68377035587136177f847c00; inferred public-preview contract; qualification unknown.
"use strict";
class AccessSystem {
  constructor(parents) {
    const children = new Map(Object.keys(parents).map(name => [name, []]));
    let root;
    for (const [name, parent] of Object.entries(parents)) {
      if (parent === null) root = name; else children.get(parent).push(name);
    }
    this.bounds = new Map(); this.allowed = new Map();
    const stack = [[root, false]]; let counter = 0;
    while (stack.length) {
      const [name, leaving] = stack.pop();
      if (leaving) this.bounds.get(name)[1] = counter;
      else {
        this.bounds.set(name, [counter++, null]); stack.push([name, true]);
        const row = children.get(name);
        for (let i = row.length - 1; i >= 0; i--) stack.push([row[i], false]);
      }
    }
  }
  grant(advertiser, region) {
    const ranges = [...(this.allowed.get(advertiser) || []), this.bounds.get(region)].sort((a,b) => a[0]-b[0]);
    const merged = [];
    for (const [left, right] of ranges) {
      if (merged.length && left <= merged[merged.length-1][1]) merged[merged.length-1][1] = Math.max(merged[merged.length-1][1], right);
      else merged.push([left, right]);
    }
    this.allowed.set(advertiser, merged);
  }
  revoke(advertiser, region) {
    const [low, high] = this.bounds.get(region), result = [];
    for (const [left, right] of this.allowed.get(advertiser) || []) {
      if (right <= low || high <= left) result.push([left, right]);
      else {
        if (left < low) result.push([left, low]);
        if (high < right) result.push([high, right]);
      }
    }
    this.allowed.set(advertiser, result);
  }
  canAccess(advertiser, region) {
    const x = this.bounds.get(region)[0], ranges = this.allowed.get(advertiser) || [];
    let low = 0, high = ranges.length;
    while (low < high) { const mid = Math.floor((low+high)/2); if (ranges[mid][0] <= x) low = mid+1; else high = mid; }
    return low > 0 && x < ranges[low-1][1];
  }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "AccessSystem") throw new Error("exact constructor trace required");
  const instance = new AccessSystem(...argumentLists[0]), result = [null], allowed = new Set(["grant", "revoke", "canAccess"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.AccessSystem = AccessSystem;
