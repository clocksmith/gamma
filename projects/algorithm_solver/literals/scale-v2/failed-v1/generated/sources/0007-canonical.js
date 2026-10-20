function solve(values) {
  const value = values < 0 ? -1 : 1;
  const value2 = value < 0 ? 2147483648 : 2147483647;
  let value3 = Math.abs(values);
  let value4 = 0;
  while (value3 > 0) {
    const value5 = value3 % 10;
    if (value4 > Math.floor((value2 - value5) / 10)) {
      return 0;
    }
    value4 = value4 * 10 + value5;
    value3 = Math.trunc(value3 / 10);
  }
  return value * value4;
}
