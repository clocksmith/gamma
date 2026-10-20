function solve(values, other) {
  let minimum = values[0];
  let maximum = values[0];
  for (const value of values) {
    minimum = Math.min(minimum, value);
    maximum = Math.max(maximum, value);
  }
  return Math.max(0, maximum - minimum - other * 2);
}
