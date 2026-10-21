function solve(values, other) {
  function helper(values2) {
    let value = 0;
    let value2 = values.length;
    while (value < value2) {
      const value3 = value + Math.floor((value2 - value) / 2);
      if (values[value3] < other || values2 && values[value3] === other) {
        value = value3 + 1;
      } else {
        value2 = value3;
      }
    }
    return value;
  }
  const index = helper(false);
  if (index === values.length || values[index] !== other) {
    return [
      -1,
      -1
    ];
  }
  return [
    index,
    helper(true) - 1
  ];
}
