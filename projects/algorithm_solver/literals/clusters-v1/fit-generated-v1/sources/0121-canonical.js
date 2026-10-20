function solve(values) {
  if (values.length === 0) {
    return 0;
  }
  let minimum = values[0];
  let maximum = 0;
  for (const value of values) {
    const value2 = value - minimum;
    if (value2 > maximum) {
      maximum = value2;
    }
    if (value < minimum) {
      minimum = value;
    }
  }
  return maximum;
}
