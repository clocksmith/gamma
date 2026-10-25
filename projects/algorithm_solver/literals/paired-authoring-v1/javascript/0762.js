class Solution {
  countPrimeSetBits(left, right) {
    const primes = new Set([2, 3, 5, 7, 11, 13, 17, 19]);
    let result = 0;
    for (let value = left; value <= right; value += 1) {
      let remaining = value;
      let bits = 0;
      while (remaining > 0) {
        bits += remaining % 2;
        remaining = Math.floor(remaining / 2);
      }
      if (primes.has(bits)) {
        result += 1;
      }
    }
    return result;
  }
}
