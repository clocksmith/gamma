// Original hack2hire:67fd508ed2adf72ba62b0ec4; inferred public-preview contract; qualification unknown.
"use strict";
function shiftTimeline(schedules) {
  const order = [...new Set(schedules.map(row => row[0]))], events = new Map(), counts = new Map(), result = [];
  const add = (time,name,delta) => { if (!events.has(time)) events.set(time,new Map()); const row = events.get(time); row.set(name,(row.get(name)||0)+delta); };
  for (const [name,start,end] of schedules) { add(start,name,1); add(end,name,-1); }
  const times = [...events.keys()].sort((a,b) => a-b);
  for (let i = 0; i+1 < times.length; i++) {
    const start = times[i], end = times[i+1];
    for (const [name,delta] of events.get(start)) counts.set(name,(counts.get(name)||0)+delta);
    const working = order.filter(name => (counts.get(name)||0) > 0); if (!working.length) continue;
    const last = result[result.length-1];
    if (last && last[1] === start && last[2].length === working.length && last[2].every((v,j) => v === working[j])) last[1] = end;
    else result.push([start,end,working]);
  }
  return result;
}

const solve = shiftTimeline;
module.exports = solve;
module.exports.shiftTimeline = shiftTimeline;
module.exports.Solution = class { shiftTimeline(...args) { return shiftTimeline(...args); } };
