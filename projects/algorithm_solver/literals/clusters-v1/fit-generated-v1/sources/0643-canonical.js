function solve(values, other) {
  let total = 0;
  for (let index = 0; index < other; index += 1) {
    total += values[index];
  }
  let maximum = total;
  for (let index2 = other; index2 < values.length; index2 += 1) {
    total += values[index2] - values[index2 - other];
    if (total > maximum) {
      maximum = total;
    }
  }
  return maximum / other;
}
