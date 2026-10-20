function solve(values, other) {
  const items = Array.from(values);
  const count = items.length;
  const items2 = Array(count).fill(count);
  let index = -count;
  for (let index3 = 0; index3 < count; index3 += 1) {
    if (items[index3] === other) {
      index = index3;
    }
    const value = index3 - index;
    if (value < items2[index3]) {
      items2[index3] = value;
    }
  }
  let index2 = 2 * count;
  for (let index4 = count - 1; index4 >= 0; index4 -= 1) {
    if (items[index4] === other) {
      index2 = index4;
    }
    const value2 = index2 - index4;
    if (value2 < items2[index4]) {
      items2[index4] = value2;
    }
  }
  return items2;
}
