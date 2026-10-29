"use strict";
// Hack2Hire 68fd47ba47bea664c0bba33c (Circular Prime Number Check) over an INFERRED spec; qualification unknown.

function isPrime(n) {
  if (n < 2) return false;
  if (n < 4) return true;
  if (n % 2 === 0 || n % 3 === 0) return false;
  for (let d = 5; d * d <= n; d += 6) if (n % d === 0 || n % (d + 2) === 0) return false;
  return true;
}

function solve(n) {
  let digits = 1, power = 1;
  while (power * 10 <= n) { power *= 10; digits++; }
  let r = n;
  for (let i = 0; i < digits; i++) {
    if (!isPrime(r)) return false;
    r = (r % power) * 10 + Math.floor(r / power);
  }
  return true;
}

function isCircularPrime(n) { return solve(n); }

module.exports = solve;
module.exports.isCircularPrime = isCircularPrime;
