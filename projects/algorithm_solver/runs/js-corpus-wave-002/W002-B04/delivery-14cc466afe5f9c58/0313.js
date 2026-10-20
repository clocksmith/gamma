function nthSuperUglyNumber(n, primes) {
  const ugly = [1], indices = Array(primes.length).fill(0);
  while (ugly.length < n) {
    let next = Infinity;
    for (let i = 0; i < primes.length; i++) next = Math.min(next, primes[i] * ugly[indices[i]]);
    ugly.push(next);
    for (let i = 0; i < primes.length; i++) if (primes[i] * ugly[indices[i]] === next) indices[i]++;
  }
  return ugly[n - 1];
}
