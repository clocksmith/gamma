'use strict';

// 972. Equal Rational Numbers.
// Exact BigInt arithmetic; cross-products can exceed Number's safe integer range.
function fractionOf(text) {
  const dot = text.indexOf('.');
  if (dot < 0) return [BigInt(text), 1n];
  const whole = text.slice(0, dot);
  const fraction = text.slice(dot + 1);
  const opening = fraction.indexOf('(');
  const prefix = opening < 0 ? fraction : fraction.slice(0, opening);
  const scale = 10n ** BigInt(prefix.length);
  const numerator = BigInt(whole) * scale + BigInt(prefix || '0');
  if (opening < 0) return [numerator, scale];
  const repeat = fraction.slice(opening + 1, -1);
  const cycle = 10n ** BigInt(repeat.length) - 1n;
  return [numerator * cycle + BigInt(repeat), scale * cycle];
}

function solve(s, t) {
  const [leftNum, leftDen] = fractionOf(s);
  const [rightNum, rightDen] = fractionOf(t);
  return leftNum * rightDen === rightNum * leftDen;
}

const isRationalEqual = solve;
class Solution {
  isRationalEqual(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isRationalEqual };
