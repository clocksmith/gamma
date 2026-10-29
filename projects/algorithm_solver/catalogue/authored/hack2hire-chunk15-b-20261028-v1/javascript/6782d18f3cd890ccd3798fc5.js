"use strict";
// Hack2Hire 6782d18f3cd890ccd3798fc5 (Find All 5-Minute Intervals) over an INFERRED spec; qualification unknown.

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const WEEK = 7 * 24 * 60;

function parse(text) {
  const [day, clock, half] = text.split(" ");
  const [hour, minute] = clock.split(":");
  let h = Number(hour) % 12;
  if (half === "PM") h += 12;
  return DAYS.indexOf(day) * 1440 + h * 60 + Number(minute);
}

function render(t) {
  t %= WEEK;
  const day = Math.floor(t / 1440), rest = t % 1440;
  const h = Math.floor(rest / 60), minute = rest % 60;
  let shown = h % 12;
  if (shown === 0) shown = 12;
  return DAYS[day] + " " + String(shown) + ":" + (minute < 10 ? "0" : "") + String(minute) + (h < 12 ? " AM" : " PM");
}

function solve(start, end) {
  const a = parse(start);
  let b = parse(end);
  if (b < a) b += WEEK;
  let t = Math.floor((a + 4) / 5) * 5;
  const result = [];
  while (t <= b) {
    result.push(render(t));
    t += 5;
  }
  return result;
}

function fiveMinuteIntervals(start, end) { return solve(start, end); }

module.exports = solve;
module.exports.fiveMinuteIntervals = fiveMinuteIntervals;
