function solve(values) {
  const value = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const value2 = 'abcdefghijklmnopqrstuvwxyz';
  const result = [];
  for (const value3 of values) {
    const index = value.indexOf(value3);
    if (index >= 0) {
      result.push(value2[index]);
    } else {
      result.push(value3);
    }
  }
  return result.join('');
}
