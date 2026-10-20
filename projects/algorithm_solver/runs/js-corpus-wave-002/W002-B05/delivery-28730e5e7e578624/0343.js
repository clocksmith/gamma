function integerBreak(n) {
  if (n <= 3) return n - 1;
  let product = 1;
  let remaining = n;
  while (remaining > 4) {
    product *= 3;
    remaining -= 3;
  }
  return product * remaining;
}
