class Solution {
  numPrimeArrangements(n) {
    const prime = Array(n + 1).fill(true);
    prime[0] = false;
    prime[1] = false;
    let candidate = 2;
    while (candidate * candidate <= n) {
      if (prime[candidate]) {
        let multiple = candidate * candidate;
        while (multiple <= n) {
          prime[multiple] = false;
          multiple += candidate;
        }
      }
      candidate += 1;
    }
    let primeCount = 0;
    for (const isPrime of prime) {
      if (isPrime) {
        primeCount += 1;
      }
    }
    let result = 1;
    const modulus = 1000000007;
    for (const count of [primeCount, n - primeCount]) {
      for (let factor = 2; factor <= count; factor += 1) {
        result = (result * factor) % modulus;
      }
    }
    return result;
  }
}
