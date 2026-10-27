/**
 * 3793. Find Users with High Token Usage
 * Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
 * Signature: solve(prompts).
 * Algorithm: Count prompts and exact token totals; require a prompt above the unrounded mean; round only output.
 * Complexity: O(n log n) time; O(n) space.
 * Numeric semantics: Safe JSON integer inputs; exact Python integer / JavaScript BigInt aggregates and ratios. Rounded decimal outputs are fixed-point strings with half-away-from-zero rounding; integer outputs stay numbers.
 * Mutation: Input tables and row objects remain unchanged; output rows are fresh objects.
 * Interface: Proposed mock-relations/v1: synchronous solve(tableRows), list of dictionaries / array of objects with original SQL column names. Not native Pandas, a SQL engine, Mox, or a qualified Gamma adapter.
 * Specification: https://leetcode.com/problems/find-users-with-high-token-usage/description/
 * Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3700-3799/3793.Find%20Users%20with%20High%20Token%20Usage/README_EN.md
 * Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
 * New readable implementations; no third-party source bodies copied verbatim.
 * No protected tests or private reference implementations used.
 * Contract note: avg_tokens is a two-decimal string. Filter uses exact max*count > sum; ordering uses the rounded displayed average, then user ID ascending.
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


function solve(prompts) {
  checkTable(prompts, { user_id: "int", prompt: "str", tokens: "int" }, ["user_id", "prompt"]);
  const groups = new Map();
  for (const row of prompts) {
    if (row.tokens < 0) throw new RangeError("Token count must be nonnegative.");
    if (!groups.has(row.user_id)) groups.set(row.user_id, { count: 0, total: 0n, maximum: 0n });
    const stats = groups.get(row.user_id);
    const tokens = BigInt(row.tokens);
    stats.count += 1;
    stats.total += tokens;
    if (tokens > stats.maximum) stats.maximum = tokens;
  }
  const result = [];
  for (const [user, stats] of groups) {
    if (stats.count >= 3 && stats.maximum * BigInt(stats.count) > stats.total) {
      const units = roundedUnits(stats.total, stats.count);
      result.push({ units, row: { user_id: user, prompt_count: stats.count, avg_tokens: fixedText(units) } });
    }
  }
  result.sort((left, right) => compareInteger(right.units, left.units) || compareInteger(left.row.user_id, right.row.user_id));
  return result.map(item => item.row);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { solve };
}
