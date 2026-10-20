function solve(values) {
  const value = {};
  let count = 0;
  for (const value2 of values) {
    const value3 = value2.split('@');
    const value4 = value3[0];
    const value5 = value3[1];
    const items = [];
    for (const value7 of value4) {
      if (value7 === '.') {
        continue;
      }
      if (value7 === '+') {
        break;
      }
      items.push(value7);
    }
    const value6 = '$' + items.join('') + '@' + value5;
    if (!value[value6]) {
      count += 1;
      value[value6] = true;
    }
  }
  return count;
}
