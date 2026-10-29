"use strict";

class NestedInteger {
  constructor(value) {
    if (value === undefined) {
      this._isInt = false;
      this._val = null;
      this._list = [];
    } else {
      this._isInt = true;
      this._val = Number(value);
      this._list = [];
    }
  }
  isInteger() { return this._isInt; }
  getInteger() { return this._isInt ? this._val : null; }
  setInteger(value) { this._isInt = true; this._val = Number(value); }
  add(elem) { this._list.push(elem); }
  getList() { return this._isInt ? [] : this._list; }
  toPlain() {
    if (this._isInt) return this._val;
    return this._list.map((x) => x.toPlain());
  }
}

function parseNested(s) {
  if (s[0] !== "[") return new NestedInteger(Number(s));
  const stack = [];
  let num = 0;
  let sign = 1;
  let inNum = false;
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    if (ch === "[") {
      stack.push(new NestedInteger());
    } else if (ch === "-") {
      sign = -1;
    } else if (ch >= "0" && ch <= "9") {
      num = num * 10 + (ch.charCodeAt(0) - 48);
      inNum = true;
    } else if (ch === "," || ch === "]") {
      if (inNum) {
        stack[stack.length - 1].add(new NestedInteger(sign * num));
        num = 0;
        sign = 1;
        inNum = false;
      }
      if (ch === "]" && stack.length > 1) {
        const top = stack.pop();
        stack[stack.length - 1].add(top);
      }
    }
  }
  return stack[0];
}

function solve(s) {
  return parseNested(s).toPlain();
}

function deserialize(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.deserialize = deserialize;
module.exports.NestedInteger = NestedInteger;
