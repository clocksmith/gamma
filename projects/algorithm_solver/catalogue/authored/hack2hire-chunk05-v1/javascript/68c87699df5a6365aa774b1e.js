// Original hack2hire:68c87699df5a6365aa774b1e; inferred public-preview contract; qualification unknown.
"use strict";
class CustomerSupportSystem {
  constructor() { this.all = new Map(); this.months = new Map(); }
  record(agentId, score, month) {
    if (!this.months.has(month)) this.months.set(month, new Map());
    for (const target of [this.all, this.months.get(month)]) {
      const [sum, count] = target.get(agentId) || [0n, 0n];
      target.set(agentId, [sum + BigInt(score), count + 1n]);
    }
  }
  rank(month) {
    const table = month === null ? this.all : this.months.get(month) || new Map();
    const names = [...table.keys()].sort((a, b) => {
      const [x, nx] = table.get(a), [y, ny] = table.get(b), difference = x * ny - y * nx;
      return difference > 0n ? -1 : difference < 0n ? 1 : a < b ? -1 : a > b ? 1 : 0;
    });
    return names.map(name => {
      const [sum, count] = table.get(name);
      let a = sum < 0n ? -sum : sum, b = count;
      while (b) [a, b] = [b, a % b];
      return [name, sum / a, count / a];
    });
  }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "CustomerSupportSystem") throw new Error("exact constructor trace required");
  const instance = new CustomerSupportSystem(...argumentLists[0]), result = [null], allowed = new Set(["record", "rank"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.CustomerSupportSystem = CustomerSupportSystem;
