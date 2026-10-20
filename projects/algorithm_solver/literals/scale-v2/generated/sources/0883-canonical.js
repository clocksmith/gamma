function solve(values) {
  if (values.length === 0) {
    return 0;
  }
  let count = values[0].length;
  let count2 = 0;
  for (const items of values) {
    count = Math.min(count, items.length);
    let maximum = items[0];
    for (const value of items) {
      if (value > 0) {
        count2 += 1;
      }
      maximum = Math.max(maximum, value);
    }
    count2 += maximum;
  }
  for (let index = 0; index < count; index += 1) {
    let maximum2 = values[0][index];
    for (const items2 of values) {
      maximum2 = Math.max(maximum2, items2[index]);
    }
    count2 += maximum2;
  }
  return count2;
}
