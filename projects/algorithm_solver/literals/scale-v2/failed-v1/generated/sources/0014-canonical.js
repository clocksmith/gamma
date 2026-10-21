function solve(values) {
  if (values.length === 0) {
    return '';
  }
  const items = Array.from(values[0]);
  let size = items.length;
  for (let index = 1; index < values.length && size > 0; index++) {
    const items2 = Array.from(values[index]);
    let index2 = 0;
    while (index2 < size && index2 < items2.length && items[index2] === items2[index2]) {
      index2++;
    }
    size = index2;
  }
  return items.slice(0, size).join('');
}
