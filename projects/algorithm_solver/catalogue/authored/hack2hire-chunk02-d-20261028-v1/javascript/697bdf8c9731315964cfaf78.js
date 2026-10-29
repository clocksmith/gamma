"use strict";
// Hack2Hire 697bdf8c9731315964cfaf78 (Hotel Booking Reminder, level 3) over an INFERRED spec; qualification unknown.

function compareText(a, b) { return a < b ? -1 : a > b ? 1 : 0; }

function solve(reservations, emailTouchpoints) {
  const schedule = [];
  for (const stay of reservations) {
    for (const [name, touchpoint] of Object.entries(emailTouchpoints)) {
      if (touchpoint.room_types !== undefined && !touchpoint.room_types.includes(stay.room_type)) continue;
      const anchor = stay.check_in_day + (touchpoint.anchor === "check_out" ? stay.stay_length : 0);
      const day = anchor + touchpoint.offset;
      schedule.push([day, stay.guest_name, name]);
    }
  }
  schedule.sort((x, y) => x[0] - y[0] || compareText(x[1], y[1]) || compareText(x[2], y[2]));
  return schedule;
}

function buildEmailSchedule(reservations, emailTouchpoints) { return solve(reservations, emailTouchpoints); }

module.exports = solve;
module.exports.buildEmailSchedule = buildEmailSchedule;
