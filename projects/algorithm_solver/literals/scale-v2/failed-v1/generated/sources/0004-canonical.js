function solve(values, other) {
  let items = values;
  let items2 = other;
  if (items.length > items2.length) {
    [items, items2] = [
      items2,
      items
    ];
  }
  const size = items.length;
  const size2 = items2.length;
  if (size + size2 === 0) {
    throw new RangeError('Both arrays are empty');
  }
  const left = Math.floor((size + size2 + 1) / 2);
  let index = 0;
  let index2 = size;
  while (index <= index2) {
    const value = Math.floor((index + index2) / 2);
    const value2 = left - value;
    const left2 = value === 0 ? -Infinity : items[value - 1];
    const right = value === size ? Infinity : items[value];
    const left3 = value2 === 0 ? -Infinity : items2[value2 - 1];
    const right2 = value2 === size2 ? Infinity : items2[value2];
    if (left2 <= right2 && left3 <= right) {
      const value3 = Math.max(left2, left3);
      if ((size + size2) % 2 === 1) {
        return value3;
      }
      const value4 = Math.min(right, right2);
      return value3 / 2 + value4 / 2;
    }
    if (left2 > right2) {
      index2 = value - 1;
    } else {
      index = value + 1;
    }
  }
  throw new RangeError('Inputs must be sorted in ascending order');
}
