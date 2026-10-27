'use strict';

// 535. Encode and Decode TinyURL.

class Codec {
  constructor() { this.forward = new Map(); this.reverse = new Map(); this.nextId = 0; }
  encode(longUrl) {
    if (this.forward.has(longUrl)) return this.forward.get(longUrl);
    const alphabet = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', digits = [];
    let value = this.nextId++;
    do { digits.push(alphabet[value % 62]); value = Math.floor(value / 62); } while (value > 0);
    const short = 'http://tinyurl.com/' + digits.reverse().join('');
    this.forward.set(longUrl, short); this.reverse.set(short, longUrl);
    return short;
  }
  decode(shortUrl) { return this.reverse.get(shortUrl); }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new Codec(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = Codec;

if (typeof module !== 'undefined') module.exports = { solve, Codec, Solution };
