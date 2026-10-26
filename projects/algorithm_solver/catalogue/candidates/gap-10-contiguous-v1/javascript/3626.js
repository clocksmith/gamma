/**
 * 3626. Find Stores with Inventory Imbalance
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(stores, inventory).
 * O(inventory + stores + output log output) rational operations; O(inventory) space.
 * Counts distinct product names. Equal extreme prices use product_name then inventory_id ascending as an explicit mock tie rule. Zero expensive-product stock yields a null ratio (undefined division), ordered last. Otherwise sorts on rounded displayed ratio.
 * Specification: https://leetcode.com/problems/find-stores-with-inventory-imbalance/description/
 * Consulted reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3626.Find%20Stores%20with%20Inventory%20Imbalance/README_EN.md
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
      else if (kind === 'decimal') { decimal(value); valid = true; }
      if (!valid) throw new TypeError('Invalid value for column: ' + column);
    }
    const key = JSON.stringify(primaryKey.map(column => row[column]));
    if (seen.has(key)) throw new RangeError('Duplicate primary key.');
    seen.add(key);
  }
}

function solve(stores, inventory) {
  validateRows(stores, {"store_id": "int", "store_name": "str", "location": "str"}, ["store_id"]);
  validateRows(inventory, {"inventory_id": "int", "store_id": "int", "product_name": "str", "quantity": "int", "price": "decimal"}, ["inventory_id"]);
  const groups = new Map();
  const tieBefore = (a, b) => compareText(a.row.product_name, b.row.product_name) < 0 ||
    (a.row.product_name === b.row.product_name && a.row.inventory_id < b.row.inventory_id);
  for (const row of inventory) {
    if (row.quantity < 0) throw new RangeError('Inventory quantities must be nonnegative.');
    const item = { row, price: decimal(row.price) };
    if (!groups.has(row.store_id)) groups.set(row.store_id, { products: new Set(), cheapest: item, expensive: item });
    const group = groups.get(row.store_id);
    group.products.add(row.product_name);
    const lowComparison = compareRational(item.price, group.cheapest.price);
    const highComparison = compareRational(item.price, group.expensive.price);
    if (lowComparison < 0 || (lowComparison === 0 && tieBefore(item, group.cheapest))) group.cheapest = item;
    if (highComparison > 0 || (highComparison === 0 && tieBefore(item, group.expensive))) group.expensive = item;
  }
  const result = [];
  for (const store of stores) {
    const group = groups.get(store.store_id);
    if (!group || group.products.size < 3) continue;
    const cheap = group.cheapest.row;
    const expensive = group.expensive.row;
    if (expensive.quantity >= cheap.quantity) continue;
    const ratio = expensive.quantity === 0 ? null : rational(BigInt(cheap.quantity), BigInt(expensive.quantity));
    result.push({ units: ratio === null ? null : roundedUnits(ratio), row: {
      store_id: store.store_id, store_name: store.store_name, location: store.location,
      most_exp_product: expensive.product_name, cheapest_product: cheap.product_name,
      imbalance_ratio: ratio === null ? null : roundedText(ratio),
    } });
  }
  result.sort((a, b) => {
    if (a.units === null && b.units !== null) return 1;
    if (a.units !== null && b.units === null) return -1;
    if (a.units !== b.units) return a.units > b.units ? -1 : 1;
    return compareText(a.row.store_name, b.row.store_name) || a.row.store_id - b.row.store_id;
  });
  return result.map(item => item.row);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
