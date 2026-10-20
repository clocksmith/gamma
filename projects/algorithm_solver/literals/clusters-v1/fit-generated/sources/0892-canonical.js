function solve(values) {
  let count = 0;
  for (let index = 0; index < values.length; index += 1) {
    const items = values[index];
    for (let index2 = 0; index2 < items.length; index2 += 1) {
      const value = items[index2];
      if (value !== 0) {
        count += 2 + value * 4;
        if (index > 0) {
          count -= Math.min(value, values[index - 1][index2]) * 2;
        }
        if (index2 > 0) {
          count -= Math.min(value, items[index2 - 1]) * 2;
        }
      }
    }
  }
  return count;
}
