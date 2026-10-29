"use strict";
// Hack2Hire 691f8b9d9abeeebe6fae3eb5 (Expense System, level 1) over an INFERRED spec; qualification unknown.

const FIELDS = {expense_id: 0, trip_id: 1, amount: 2, expense_type: 3, vendor_type: 4, vendor_name: 5};

function cents(text) {
  const dot = text.indexOf(".");
  if (dot < 0) return Number(text) * 100;
  return Number(text.slice(0, dot)) * 100 + Number((text.slice(dot + 1) + "00").slice(0, 2));
}

function holds(lhs, op, rhs) {
  switch (op) {
    case "<": return lhs < rhs;
    case "<=": return lhs <= rhs;
    case ">": return lhs > rhs;
    case ">=": return lhs >= rhs;
    case "==": return lhs === rhs;
    default: return lhs !== rhs;
  }
}

function solve(rules, expenses) {
  const amounts = expenses.map((e) => cents(e[2]));
  const result = [];
  for (const [kind, ruleId, field, op, value, condField, condValue] of rules) {
    const column = FIELDS[field];
    const rhs = field === "amount" ? cents(value) : value;
    const cond = condField ? FIELDS[condField] : -1;
    const trips = new Map();
    expenses.forEach((expense, index) => {
      if (cond >= 0 && expense[cond] !== condValue) return;
      if (kind === "trip") { trips.set(expense[1], (trips.get(expense[1]) || 0) + amounts[index]); return; }
      const lhs = column === 2 ? amounts[index] : expense[column];
      if (!holds(lhs, op, rhs)) result.push([ruleId, expense[0]]);
    });
    for (const [trip, total] of trips) if (!holds(total, op, rhs)) result.push([ruleId, trip]);
  }
  return result;
}

function findViolations(rules, expenses) { return solve(rules, expenses); }

module.exports = solve;
module.exports.findViolations = findViolations;
