function solve(values) {
  const items = helper2(values);
  const result = [];
  for (let index = 0; index < items.length; index += 1) {
    let value = items[index];
    if (![
        'a',
        'e',
        'i',
        'o',
        'u'
      ].includes(value.toLowerCase()[0])) {
      const items2 = Array.from(value);
      value = items2.slice(1).join('') + items2[0];
    }
    result.push(value + 'ma' + 'a'.repeat(index + 1));
  }
  return result.join(' ');
}
function helper(values2) {
  const value2 = values2.codePointAt(0);
  return value2 >= 9 && value2 <= 13 || value2 >= 28 && value2 <= 32 || value2 === 133 || value2 === 160 || value2 === 5760 || value2 >= 8192 && value2 <= 8202 || value2 === 8232 || value2 === 8233 || value2 === 8239 || value2 === 8287 || value2 === 12288;
}
function helper2(values3) {
  const items3 = [];
  let items4 = [];
  for (const value3 of values3) {
    if (helper(value3)) {
      if (items4.length > 0) {
        items3.push(items4.join(''));
        items4 = [];
      }
    } else {
      items4.push(value3);
    }
  }
  if (items4.length > 0) {
    items3.push(items4.join(''));
  }
  return items3;
}
