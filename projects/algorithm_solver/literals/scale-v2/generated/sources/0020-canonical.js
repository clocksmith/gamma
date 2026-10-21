function solve(values) {
  const items = new Map([
    [
      '(',
      ')'
    ],
    [
      '[',
      ']'
    ],
    [
      '{',
      '}'
    ]
  ]);
  const value = [];
  for (const value2 of values) {
    if (items.has(value2)) {
      value.push(items.get(value2));
    } else if (value.pop() !== value2) {
      return false;
    }
  }
  return value.length === 0;
}
