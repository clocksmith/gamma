"use strict";

class TopVotedCandidate {
  constructor(persons, times) {
    this.times = times.slice();
    const counts = new Map();
    this.leaders = new Int32Array(persons.length);
    let curLeader = -1;
    let maxVotes = 0;
    for (let i = 0; i < persons.length; i++) {
      const p = persons[i];
      const c = (counts.get(p) || 0) + 1;
      counts.set(p, c);
      if (c >= maxVotes) {
        maxVotes = c;
        curLeader = p;
      }
      this.leaders[i] = curLeader;
    }
  }

  q(t) {
    let lo = 0, hi = this.times.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (this.times[mid] <= t) lo = mid + 1;
      else hi = mid;
    }
    return this.leaders[lo - 1];
  }
}

function solve(operationNames, argumentLists) {
  const inst = new TopVotedCandidate(argumentLists[0][0], argumentLists[0][1]);
  const out = [null];
  for (let i = 1; i < operationNames.length; i++) {
    out.push(inst.q(argumentLists[i][0]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.TopVotedCandidate = TopVotedCandidate;
