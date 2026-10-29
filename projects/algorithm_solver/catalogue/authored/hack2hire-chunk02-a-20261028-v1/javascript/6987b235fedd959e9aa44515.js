"use strict";
// Hack2Hire 6987b235fedd959e9aa44515 (IPO Share Allocation); INFERRED spec; qualification unknown.
function solve(bids, totalShares) {
  const order = bids.map((_, i) => i).sort((a, b) => bids[b][2] - bids[a][2] || bids[a][3] - bids[b][3] || a - b);
  let remaining = totalShares, pos = 0;
  const unallotted = [];
  while (pos < order.length) {
    let end = pos, need = 0;
    while (end < order.length && bids[order[end]][2] === bids[order[pos]][2]) need += bids[order[end++]][1];
    if (need <= remaining) remaining -= need;
    else {
      for (let rank = 0; rank < end - pos; rank++) if (rank >= remaining) unallotted.push(bids[order[pos + rank]][0]);
      remaining = 0;
    }
    pos = end;
  }
  return unallotted.sort((a, b) => a - b);
}
function getUnallottedUsers(bids, totalShares) { return solve(bids, totalShares); }
module.exports = solve;
module.exports.getUnallottedUsers = getUnallottedUsers;
