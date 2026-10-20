function solve(values) {
  let total = 0;
  for (const value of values) {
    total += value;
  }
  let total2 = 0;
  for (let index = 0; index < values.length; index += 1) {
    total -= values[index];
    if (total2 === total) {
      return index;
    }
    total2 += values[index];
  }
  return -1;
}
