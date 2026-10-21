function solve(values, other) {
  const items = Array.from(values);
  const items2 = Array.from(other);
  let index = 0;
  let index2 = 0;
  while (index < items.length && index2 < items2.length) {
    if (items[index] !== items2[index2]) {
      return false;
    }
    let index3 = index + 1;
    while (index3 < items.length && items[index3] === items[index]) {
      index3 += 1;
    }
    let index4 = index2 + 1;
    while (index4 < items2.length && items2[index4] === items2[index2]) {
      index4 += 1;
    }
    if (index3 - index > index4 - index2) {
      return false;
    }
    index = index3;
    index2 = index4;
  }
  return index === items.length && index2 === items2.length;
}
