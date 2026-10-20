function solve(values) {
  let value = 0;
  let count = 0;
  for (const value2 of values) {
    if (count === 0) {
      value = value2;
    }
    if (value2 === value) {
      count += 1;
    } else {
      count -= 1;
    }
  }
  return value;
}
