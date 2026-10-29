"use strict";
// Hack2Hire 68c331ec1f64f4312b0a3e2d (Subscription Billing Statement) over an INFERRED spec; qualification unknown.

function leap(year) { return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0); }

function solve(plans, events) {
  if (events.length === 0) return [];
  const price = new Map(plans.map(([name, cents]) => [name, cents]));
  const year = Number(events[0][0].slice(0, 4));
  const lengths = [31, leap(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const firsts = [1];
  for (let i = 0; i < 11; i++) firsts.push(firsts[i] + lengths[i]);
  const yearEnd = firsts[11] + lengths[11];
  const dayOfYear = (date) => firsts[Number(date.slice(5, 7)) - 1] + Number(date.slice(8, 10)) - 1;
  const intervals = [];
  let active = null, since = 0;
  for (const [date, kind, name] of events) {
    const day = dayOfYear(date);
    if (active !== null) intervals.push([since, day, active]);
    active = kind === "END" ? null : name;
    since = day;
  }
  if (active !== null) intervals.push([since, yearEnd, active]);
  const numerators = new Array(12).fill(0), billed = new Array(12).fill(0);
  for (const [lo, hi, name] of intervals) {
    for (let month = 0; month < 12; month++) {
      const overlap = Math.min(hi, firsts[month] + lengths[month]) - Math.max(lo, firsts[month]);
      if (overlap > 0) {
        numerators[month] += price.get(name) * overlap;
        billed[month] += overlap;
      }
    }
  }
  const out = [];
  for (let month = 0; month < 12; month++) {
    if (billed[month]) {
      const days = lengths[month];
      const label = String(year).padStart(4, "0") + "-" + String(month + 1).padStart(2, "0");
      out.push([label, Math.floor((2 * numerators[month] + days) / (2 * days))]);
    }
  }
  return out;
}

function billingStatement(plans, events) { return solve(plans, events); }

module.exports = solve;
module.exports.billingStatement = billingStatement;
