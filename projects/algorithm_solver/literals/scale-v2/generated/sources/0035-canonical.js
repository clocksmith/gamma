function solve(values, other) {
  let value = 0;
  let value2 = values.length;
  while (value < value2) {
    const value3 = value + Math.floor((value2 - value) / 2);
    if (values[value3] < other) {
      value = value3 + 1;
    } else {
      value2 = value3;
    }
  }
  return value;
}
