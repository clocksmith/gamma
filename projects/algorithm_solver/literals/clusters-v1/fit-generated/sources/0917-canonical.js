function solve(values) {
  const items = Array.from(values);
  let index = 0;
  let index2 = items.length;
  while (index + 1 < index2) {
    while (index + 1 < index2 && !/^\p{L}$/u.test(items[index])) {
      index += 1;
    }
    while (index + 1 < index2 && !/^\p{L}$/u.test(items[index2 - 1])) {
      index2 -= 1;
    }
    if (index + 1 < index2) {
      const value = items[index];
      items[index] = items[index2 - 1];
      items[index2 - 1] = value;
      index += 1;
      index2 -= 1;
    }
  }
  return items.join('');
}
