function primeFactors(value) {
  const factors = [];
  let divisor = 2n;
  while (divisor * divisor <= value) {
    if (value % divisor === 0n) {
      factors.push(divisor);
      while (value % divisor === 0n) {
        value /= divisor;
      }
    }
    divisor = divisor === 2n ? 3n : divisor + 2n;
  }
  if (value > 1n) {
    factors.push(value);
  }
  return factors;
}

function modularPower(base, exponent, modulus) {
  let result = 1n;
  base %= modulus;
  while (exponent > 0n) {
    if (exponent % 2n === 1n) {
      result = result * base % modulus;
    }
    base = base * base % modulus;
    exponent /= 2n;
  }
  return result;
}

class Solution {
  smallestRepunitDivByK(k) {
    if (k % 2 === 0 || k % 5 === 0) {
      return -1;
    }
    const modulus = 9n * BigInt(k);
    let order = modulus;
    for (const factor of primeFactors(modulus)) {
      order = order / factor * (factor - 1n);
    }
    for (const factor of primeFactors(order)) {
      while (order % factor === 0n) {
        const candidate = order / factor;
        if (modularPower(10n, candidate, modulus) !== 1n) {
          break;
        }
        order = candidate;
      }
    }
    return Number(order);
  }
}
