/**
 * 3642. Find Books with Polarized Opinions
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(books, readingSessions).
 * O(sessions + books + output log output) time; O(books with sessions) state.
 * Implements the numbered session-rating criteria, without collapsing repeated readers. The 60% test is exact and precedes rounding; display-score ties use title descending. The prose mention of different readers is not treated as an additional unlisted distinct-reader constraint; confirm against Gamma before promotion.
 * Specification: https://leetcode.com/problems/find-books-with-polarized-opinions/description/
 */

function compareText(left, right) {
  const a = Array.from(left);
  const b = Array.from(right);
  for (let index = 0; index < Math.min(a.length, b.length); index += 1) {
    const difference = a[index].codePointAt(0) - b[index].codePointAt(0);
    if (difference !== 0) return difference < 0 ? -1 : 1;
  }
  return a.length - b.length;
}

function rational(numerator, denominator = 1n) {
  if (denominator === 0n) throw new RangeError('Zero rational denominator.');
  if (denominator < 0n) {
    numerator = -numerator;
    denominator = -denominator;
  }
  let a = numerator < 0n ? -numerator : numerator;
  let b = denominator;
  while (b !== 0n) [a, b] = [b, a % b];
  return { n: numerator / a, d: denominator / a };
}

function decimal(value) {
  if ((typeof value !== 'string' && typeof value !== 'number') ||
      (typeof value === 'number' && !Number.isFinite(value))) {
    throw new TypeError('Expected a finite decimal number or decimal string.');
  }
  const text = String(value);
  const match = /^([+-]?)([0-9]+)(?:\.([0-9]+))?(?:[eE]([+-]?[0-9]+))?$/.exec(text);
  if (!match || match[0] !== text || text.length > 1024) {
    throw new TypeError('Invalid mock decimal representation.');
  }
  const fraction = match[3] || '';
  const exponent = Number(match[4] || 0) - fraction.length;
  if (!Number.isSafeInteger(exponent) || Math.abs(exponent) > 1000) {
    throw new RangeError('Mock decimal exponent exceeds the declared bound.');
  }
  let numerator = BigInt(match[2] + fraction);
  if (match[1] === '-') numerator = -numerator;
  return exponent >= 0
    ? rational(numerator * (10n ** BigInt(exponent)))
    : rational(numerator, 10n ** BigInt(-exponent));
}

function addRational(a, b) {
  return rational(a.n * b.d + b.n * a.d, a.d * b.d);
}

function subtractRational(a, b) {
  return rational(a.n * b.d - b.n * a.d, a.d * b.d);
}

function divideRational(a, b) {
  return rational(a.n * b.d, a.d * b.n);
}

function compareRational(a, b) {
  const difference = a.n * b.d - b.n * a.d;
  return difference < 0n ? -1 : difference > 0n ? 1 : 0;
}

function roundedUnits(value, places = 2) {
  const magnitude = (value.n < 0n ? -value.n : value.n) * (10n ** BigInt(places));
  let quotient = magnitude / value.d;
  if (2n * (magnitude % value.d) >= value.d) quotient += 1n;
  return value.n < 0n ? -quotient : quotient;
}

function unitsText(units, places, trim = false) {
  const sign = units < 0n ? '-' : '';
  let digits = (units < 0n ? -units : units).toString();
  if (places === 0) return sign + digits;
  digits = digits.padStart(places + 1, '0');
  let text = sign + digits.slice(0, -places) + '.' + digits.slice(-places);
  if (trim) text = text.replace(/0+$/, '').replace(/\.$/, '');
  return text;
}

function roundedText(value, places = 2) {
  return unitsText(roundedUnits(value, places), places);
}

function exactDecimalText(value) {
  let denominator = value.d;
  let twos = 0;
  let fives = 0;
  while (denominator % 2n === 0n) { denominator /= 2n; twos += 1; }
  while (denominator % 5n === 0n) { denominator /= 5n; fives += 1; }
  if (denominator !== 1n) throw new RangeError('Nonterminating decimal requires an explicit rounding rule.');
  const places = Math.max(twos, fives);
  const units = value.n * (10n ** BigInt(places)) / value.d;
  return unitsText(units, places, true);
}

function validateRows(rows, schema, primaryKey) {
  if (!Array.isArray(rows)) throw new TypeError('Expected a table as an array of row objects.');
  const seen = new Set();
  for (const row of rows) {
    if (row === null || typeof row !== 'object' || Array.isArray(row)) {
      throw new TypeError('Expected a row object.');
    }
    for (const [column, declared] of Object.entries(schema)) {
      if (!Object.prototype.hasOwnProperty.call(row, column)) throw new TypeError('Missing column: ' + column);
      const value = row[column];
      if (value === null && declared.endsWith('?')) continue;
      const kind = declared.replace(/\?$/, '');
      let valid = false;
      if (kind === 'int') valid = Number.isSafeInteger(value);
      else if (kind === 'str') valid = typeof value === 'string' && !Array.from(value).some(c => { const p = c.codePointAt(0); return p >= 0xD800 && p <= 0xDFFF; });
      if (!valid) throw new TypeError('Invalid value for column: ' + column);
    }
    const key = JSON.stringify(primaryKey.map(column => row[column]));
    if (seen.has(key)) throw new RangeError('Duplicate primary key.');
    seen.add(key);
  }
}

function solve(books, readingSessions) {
  validateRows(books, {"book_id": "int", "title": "str", "author": "str", "genre": "str", "pages": "int"}, ["book_id"]);
  validateRows(readingSessions, {"session_id": "int", "book_id": "int", "reader_name": "str", "pages_read": "int", "session_rating": "int"}, ["session_id"]);
  const groups = new Map();
  for (const session of readingSessions) {
    const rating = session.session_rating;
    if (rating < 1 || rating > 5) throw new RangeError('Rating is outside 1 through 5.');
    if (!groups.has(session.book_id)) groups.set(session.book_id, { count: 0, extreme: 0, low: rating, high: rating });
    const group = groups.get(session.book_id);
    group.count += 1;
    if (rating <= 2 || rating >= 4) group.extreme += 1;
    group.low = Math.min(group.low, rating);
    group.high = Math.max(group.high, rating);
  }
  const result = [];
  for (const book of books) {
    const group = groups.get(book.book_id);
    if (!group || group.count < 5 || group.low > 2 || group.high < 4 || 5 * group.extreme < 3 * group.count) continue;
    const score = rational(BigInt(group.extreme), BigInt(group.count));
    result.push({ units: roundedUnits(score), row: {
      book_id: book.book_id, title: book.title, author: book.author, genre: book.genre, pages: book.pages,
      rating_spread: group.high - group.low, polarization_score: roundedText(score),
    } });
  }
  result.sort((a, b) => a.units !== b.units ? (a.units > b.units ? -1 : 1) :
    compareText(b.row.title, a.row.title) || a.row.book_id - b.row.book_id);
  return result.map(item => item.row);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
