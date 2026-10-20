function trailingZeroes(n) {
  let value = n;
  let zeroes = 0;

  while (value >= 5) {
    value = Math.floor(value / 5);
    zeroes += value;
  }

  return zeroes;
}
