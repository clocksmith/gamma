function solve(values) {
  let minimum = Math.min(...values);
  let total = 0;
  while (minimum) {
    total += (minimum % 10 + 10) % 10;
    minimum = Math.floor(minimum / 10);
  }
  return total & 1 ^ 1;
}
