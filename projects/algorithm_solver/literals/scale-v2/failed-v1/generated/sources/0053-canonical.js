function solve(values) {
  let maximum = values[0], total = 0;
  for (const value of values) {
    total = Math.max(value, total + value);
    maximum = Math.max(maximum, total);
  }
  return maximum;
}
