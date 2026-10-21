function solve(values) {
  const items = [];
  for (const value of values) {
    items.push(Array.from(value));
  }
  const count = items[0].length;
  let count2 = 0;
  for (let index = 0; index < count; index += 1) {
    for (let index2 = 1; index2 < items.length; index2 += 1) {
      if (items[index2][index].codePointAt(0) < items[index2 - 1][index].codePointAt(0)) {
        count2 += 1;
        break;
      }
    }
  }
  return count2;
}
