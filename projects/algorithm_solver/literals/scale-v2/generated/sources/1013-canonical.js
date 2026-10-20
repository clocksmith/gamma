function solve(values) {
  let total = 0;
  for (const value2 of values) {
    total += value2;
  }
  if (total % 3 !== 0) {
    return false;
  }
  const value = total / 3;
  let count = 0;
  let total2 = 0;
  for (const value3 of values) {
    total2 += value3;
    if (total2 === value) {
      count += 1;
      total2 = 0;
    }
  }
  return count >= 3;
}
