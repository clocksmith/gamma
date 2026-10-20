function countBits(n) {
  const result = new Array(n + 1).fill(0);
  for (let value = 1; value <= n; value++) {
    result[value] = result[Math.floor(value / 2)] + (value % 2);
  }
  return result;
}
