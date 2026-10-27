/**
 * 3716. Find Churn Risk Customers
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(subscription_events).
 * Algorithm: Sort each user's event history; compare final active amount with exact historical maximum and first-to-last duration.
 * Complexity: O(n log n) time; O(n) space.
 * Numeric semantics: Safe JSON integer inputs; exact Python integer / JavaScript BigInt aggregates and ratios. Rounded decimal outputs are fixed-point strings with half-away-from-zero rounding; integer outputs stay numbers.
 * Mutation: Input tables and row objects remain unchanged; output rows are fresh objects.
 * Interface: Proposed mock-relations/v1: synchronous solve(tableRows), list of dictionaries / array of objects with original SQL column names. Not native Pandas, a SQL engine, Mox, or a qualified Gamma adapter.
 * Specification: https://leetcode.com/problems/find-churn-risk-customers/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3716.Find%20Churn%20Risk%20Customers/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: Duration is last-event date minus first-event date, not wall-clock today. Same-day events use event_id ascending as an explicit adapter tie rule; not a recovered Gamma contract. Decimal result amounts are canonical exact strings.
 */

function dateDay(value) {
  if (typeof value !== "string" || !/^[0-9]{4}-[0-9]{2}-[0-9]{2}$/.test(value)) throw new TypeError("Expected normalized Gregorian YYYY-MM-DD.");
  const [year, month, day] = value.split("-").map(Number);
  if (year < 1 || month < 1 || month > 12 || day < 1 || day > 31) throw new RangeError("Invalid date.");
  const parsed = new Date(0);
  parsed.setUTCFullYear(year, month - 1, day);
  parsed.setUTCHours(0, 0, 0, 0);
  if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) throw new RangeError("Invalid date.");
  return parsed.getTime() / 86400000;
}

function timestampSeconds(value) {
  if (typeof value !== "string" || !/^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$/.test(value)) throw new TypeError("Expected YYYY-MM-DD HH:MM:SS without timezone or fractional seconds.");
  const [hour, minute, second] = value.slice(11).split(":").map(Number);
  if (hour > 23 || minute > 59 || second > 59) throw new RangeError("Invalid timestamp clock.");
  return dateDay(value.slice(0, 10)) * 86400 + hour * 3600 + minute * 60 + second;
}

function decimalParts(value) {
  if (!(typeof value === "string" || (typeof value === "number" && Number.isFinite(value)))) throw new TypeError("Expected a decimal string or finite number.");
  const text = String(value);
  if (text.length > 1024) throw new RangeError("Decimal text exceeds the adapter bound.");
  const match = /^([+-]?)([0-9]+)(?:\.([0-9]*))?(?:[eE]([+-]?[0-9]+))?$/.exec(text);
  if (!match) throw new TypeError("Invalid decimal.");
  const fractional = match[3] || "";
  const exponent = Number(match[4] || "0");
  if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > 1000) throw new RangeError("Decimal exponent exceeds the adapter bound.");
  let coefficient = BigInt(match[2] + fractional);
  if (match[1] === "-") coefficient = -coefficient;
  let scale = fractional.length - exponent;
  if (scale < 0) {
    coefficient *= 10n ** BigInt(-scale);
    scale = 0;
  }
  return [coefficient, scale];
}

function decimalText(coefficient, scale) {
  if (coefficient === 0n) return "0";
  const negative = coefficient < 0n;
  let digits = (negative ? -coefficient : coefficient).toString();
  if (scale > 0) {
    digits = digits.padStart(scale + 1, "0");
    digits = (digits.slice(0, -scale) + "." + digits.slice(-scale)).replace(/0+$/, "").replace(/\.$/, "");
  }
  return (negative ? "-" : "") + digits;
}

function roundedUnits(numerator, denominator, places = 2) {
  numerator = BigInt(numerator);
  denominator = BigInt(denominator);
  if (denominator <= 0n) throw new RangeError("Expected positive denominator.");
  const negative = numerator < 0n;
  const scaled = (negative ? -numerator : numerator) * (10n ** BigInt(places));
  let quotient = scaled / denominator;
  if (2n * (scaled % denominator) >= denominator) quotient += 1n;
  return negative ? -quotient : quotient;
}

function fixedText(units, places = 2) {
  const negative = units < 0n;
  const digits = (negative ? -units : units).toString().padStart(places + 1, "0");
  const text = places ? digits.slice(0, -places) + "." + digits.slice(-places) : digits;
  return (negative ? "-" : "") + text;
}

function compareText(left, right) {
  const first = Array.from(left);
  const second = Array.from(right);
  for (let index = 0; index < Math.min(first.length, second.length); index += 1) {
    const difference = first[index].codePointAt(0) - second[index].codePointAt(0);
    if (difference !== 0) return difference < 0 ? -1 : 1;
  }
  return first.length - second.length;
}

function compareInteger(left, right) {
  return left < right ? -1 : left > right ? 1 : 0;
}

function checkTable(rows, schema, primaryKey) {
  if (!Array.isArray(rows)) throw new TypeError("Expected an array of row objects.");
  const seen = new Set();
  for (const row of rows) {
    if (row === null || typeof row !== "object" || Array.isArray(row)) throw new TypeError("Expected a row object.");
    for (const [column, declared] of Object.entries(schema)) {
      if (!Object.prototype.hasOwnProperty.call(row, column)) throw new TypeError("Missing column: " + column);
      const value = row[column];
      if (value === null && declared.endsWith("?")) continue;
      const kind = declared.replace(/\?$/, "");
      if (kind === "int") {
        if (!Number.isSafeInteger(value)) throw new TypeError("Expected a safe JSON integer: " + column);
      } else if (kind === "str") {
        if (typeof value !== "string" || Array.from(value).some(character => { const code = character.codePointAt(0); return code >= 0xD800 && code <= 0xDFFF; })) throw new TypeError("Expected a Unicode scalar string: " + column);
      } else if (kind === "date") dateDay(value);
      else if (kind === "datetime") timestampSeconds(value);
      else if (kind === "decimal") decimalParts(value);
      else throw new TypeError("Unknown adapter schema type.");
    }
    const identity = JSON.stringify(primaryKey.map(column => row[column]));
    if (seen.has(identity)) throw new RangeError("Duplicate primary key.");
    seen.add(identity);
  }
}


function solve(subscription_events) {
  checkTable(subscription_events, { event_id: "int", user_id: "int", event_date: "date", event_type: "str", plan_name: "str?", monthly_amount: "decimal" }, ["event_id"]);
  const groups = new Map();
  for (const row of subscription_events) {
    if (!["start", "upgrade", "downgrade", "cancel"].includes(row.event_type)) throw new TypeError("Unknown subscription event type.");
    if (row.event_type !== "cancel" && row.plan_name === null) throw new TypeError("Active event needs a plan name.");
    const [coefficient, scale] = decimalParts(row.monthly_amount);
    if (coefficient < 0n) throw new RangeError("Subscription amount cannot be negative.");
    if (!groups.has(row.user_id)) groups.set(row.user_id, []);
    groups.get(row.user_id).push({ row, coefficient, scale });
  }
  const result = [];
  for (const [user, events] of groups) {
    events.sort((left, right) => compareText(left.row.event_date, right.row.event_date) || compareInteger(left.row.event_id, right.row.event_id));
    const last = events[events.length - 1].row;
    if (last.event_type === "cancel" || !events.some(item => item.row.event_type === "downgrade")) continue;
    let scale = 0;
    for (const item of events) scale = Math.max(scale, item.scale);
    const amounts = events.map(item => item.coefficient * (10n ** BigInt(scale - item.scale)));
    let maximum = amounts[0];
    for (const amount of amounts) if (amount > maximum) maximum = amount;
    const current = amounts[amounts.length - 1];
    const days = dateDay(last.event_date) - dateDay(events[0].row.event_date);
    if (2n * current < maximum && days >= 60) {
      result.push({ user_id: user, current_plan: last.plan_name,
        current_monthly_amount: decimalText(current, scale), max_historical_amount: decimalText(maximum, scale), days_as_subscriber: days });
    }
  }
  return result.sort((left, right) => right.days_as_subscriber - left.days_as_subscriber || compareInteger(left.user_id, right.user_id));
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve };
}
