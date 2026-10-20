function solve(values, other) {
  const items = values.split('');
  for (let value = 0; value < items.length; value += 2 * other) {
    let index = value;
    let index2 = value + other;
    if (index2 > items.length) {
      index2 = items.length;
    }
    while (index + 1 < index2) {
      index2 -= 1;
      const value2 = items[index];
      items[index] = items[index2];
      items[index2] = value2;
      index += 1;
    }
  }
  return items.join('');
}
