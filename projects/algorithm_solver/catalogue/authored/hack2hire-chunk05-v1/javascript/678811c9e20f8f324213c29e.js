// Original hack2hire:678811c9e20f8f324213c29e; inferred public-preview contract; qualification unknown.
"use strict";
class MeetingScheduler {
  constructor(rooms) { this.rooms = rooms.slice(); this.bookings = new Map(rooms.map(r => [r, []])); }
  book(start, end) {
    for (const room of this.rooms) {
      const rows = this.bookings.get(room); let low = 0, high = rows.length;
      while (low < high) { const mid = Math.floor((low+high)/2); if (rows[mid][0] < start) low = mid+1; else high = mid; }
      if (low && rows[low-1][1] > start || low < rows.length && rows[low][0] < end) continue;
      rows.splice(low, 0, [start, end]); return room;
    }
    return null;
  }
  schedule(room) { return this.bookings.get(room).map(row => row.slice()); }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "MeetingScheduler") throw new Error("exact constructor trace required");
  const instance = new MeetingScheduler(...argumentLists[0]), result = [null], allowed = new Set(["book", "schedule"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.MeetingScheduler = MeetingScheduler;
