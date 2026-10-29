"use strict";

const ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ";

function toBase62(num) {
  if (num === 0) return "0";
  let out = "";
  let n = num;
  while (n > 0) {
    out = ALPHABET[n % 62] + out;
    n = Math.floor(n / 62);
  }
  return out;
}

class Codec {
  constructor() {
    this.urlToCode = new Map();
    this.codeToUrl = new Map();
    this.counter = 1;
  }
  encode(longUrl) {
    let code = this.urlToCode.get(longUrl);
    if (code === undefined) {
      code = toBase62(this.counter++);
      this.urlToCode.set(longUrl, code);
      this.codeToUrl.set(code, longUrl);
    }
    return "http://tinyurl.com/" + code;
  }
  decode(shortUrl) {
    const slash = shortUrl.lastIndexOf("/");
    const code = shortUrl.slice(slash + 1);
    return this.codeToUrl.get(code);
  }
}

const defaultCodec = new Codec();
function encode(longUrl) { return defaultCodec.encode(longUrl); }
function decode(shortUrl) { return defaultCodec.decode(shortUrl); }

function solve(url) {
  const codec = new Codec();
  return codec.decode(codec.encode(url));
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Codec = Codec;
module.exports.encode = encode;
module.exports.decode = decode;
