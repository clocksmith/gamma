"use strict";
// Hack2Hire 6ace8eea2e3a0349b3a8e1d4 (Request Routing System, level 2) over an INFERRED spec; qualification unknown.

const INTEGER = /^-?(0|[1-9][0-9]{0,8})$/;
const LEVEL = 2;

function parse(token, low, high) {
  if (!INTEGER.test(token)) return null;
  const value = Number(token) + 0;
  return value >= low && value <= high ? value : null;
}

class RequestRouter {
  constructor() { this.index = new Map(); this.names = []; this.lat = []; this.lon = []; this.cap = []; this.up = []; this.load = []; }

  processCommand(command) {
    const tokens = command.split(' '), head = tokens[0], size = tokens.length;
    if (head === 'REGISTER' && size === 5) {
      const lat = parse(tokens[2], -90, 90), lon = parse(tokens[3], -180, 180), cap = parse(tokens[4], 1, 1e9);
      if (lat === null || lon === null || cap === null || this.index.has(tokens[1])) return 'ERROR';
      this.index.set(tokens[1], this.names.length);
      this.names.push(tokens[1]); this.lat.push(lat); this.lon.push(lon); this.cap.push(cap); this.up.push(true); this.load.push(0);
      return 'OK';
    }
    if (head === 'ROUTE' && size === 3) {
      const lat = parse(tokens[1], -90, 90), lon = parse(tokens[2], -180, 180);
      if (lat === null || lon === null) return 'ERROR';
      let best = -1, bestDistance = 0;
      for (let i = 0; i < this.names.length; i++) {
        if (!this.up[i] || this.load[i] >= this.cap[i]) continue;
        const dlat = this.lat[i] - lat, dlon = this.lon[i] - lon, d = dlat * dlat + dlon * dlon;
        if (best < 0 || d < bestDistance || (d === bestDistance && (this.load[i] < this.load[best] ||
            (this.load[i] === this.load[best] && this.names[i] < this.names[best])))) { best = i; bestDistance = d; }
      }
      if (best < 0) return 'ERROR';
      this.load[best] += 1;
      return this.names[best];
    }
    if (LEVEL >= 2 && (head === 'UP' || head === 'DOWN') && size === 2) {
      const i = this.index.get(tokens[1]);
      if (i === undefined) return 'ERROR';
      this.up[i] = head === 'UP';
      return 'OK';
    }
    if (LEVEL >= 3 && head === 'RELEASE' && size === 2) {
      const i = this.index.get(tokens[1]);
      if (i === undefined || this.load[i] === 0) return 'ERROR';
      this.load[i] -= 1;
      return 'OK';
    }
    return 'ERROR';
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "RequestRouter" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new RequestRouter(...argumentLists[0]);
  const allowed = new Set(["processCommand"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.RequestRouter = RequestRouter;
