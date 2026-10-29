"use strict";
// Hack2Hire 67fc7863216af53465a7221c (Work Schedule) over an INFERRED spec; qualification unknown.

function solve(pattern, workHours, dayHours) {
  const chars = pattern.split(''), slots = [];
  let fixed = 0;
  chars.forEach((ch, i) => { if (ch === '?') slots.push(i); else fixed += ch.charCodeAt(0) - 48; });
  const need = workHours - fixed, result = [];
  if (need < 0 || need > slots.length * dayHours) return result;
  function fill(index, remaining) {
    if (index === slots.length) { if (remaining === 0) result.push(chars.join('')); return; }
    const left = slots.length - index - 1;
    for (let digit = 0; digit <= Math.min(dayHours, remaining); digit++) {
      if (remaining - digit <= left * dayHours) { chars[slots[index]] = String(digit); fill(index + 1, remaining - digit); }
    }
  }
  fill(0, need);
  return result;
}

function findSchedules(pattern, workHours, dayHours) { return solve(pattern, workHours, dayHours); }

module.exports = solve;
module.exports.findSchedules = findSchedules;
