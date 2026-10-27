'use strict';
// 271. Encode and Decode Strings.
class Codec {
  encode(strs) { return strs.map(value => `${value.length}#${value}`).join(''); }
  decode(s) {
    const result = []; let index = 0;
    while (index < s.length) {
      const separator = s.indexOf('#', index);
      const length = Number(s.slice(index, separator));
      const start = separator + 1;
      result.push(s.slice(start, start + length));
      index = start + length;
    }
    return result;
  }
}
function solve(strs) { const codec = new Codec(); return codec.decode(codec.encode(strs)); }
if (typeof module !== 'undefined') module.exports = { solve, Codec };
