/**
 * 3475. DNA Pattern Recognition
 * 
 * Authored candidate. Not executed, syntax-checked, tested, or qualified.
 * Interface: mock-relations/v1 candidate; NOT a native Pandas or verified Gamma adapter.
 * Signature: solve(samples).
 * O(total sequence length + n log n) time; O(n) output space.
 * All samples are returned with independent integer indicator columns; GGGG also contains a run of at least three Gs.
 * Specification: https://leetcode.com/problems/dna-pattern-recognition/description/
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

function solve(samples) {
  validateRows(samples, {"sample_id": "int", "dna_sequence": "str", "species": "str"}, ["sample_id"]);
  return samples.map(row => ({
    sample_id: row.sample_id, dna_sequence: row.dna_sequence, species: row.species,
    has_start: Number(row.dna_sequence.startsWith('ATG')),
    has_stop: Number(['TAA', 'TAG', 'TGA'].some(codon => row.dna_sequence.endsWith(codon))),
    has_atat: Number(row.dna_sequence.includes('ATAT')),
    has_ggg: Number(row.dna_sequence.includes('GGG')),
  })).sort((a, b) => a.sample_id - b.sample_id);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
