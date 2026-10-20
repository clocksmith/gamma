function solve(values) {
  const count = values.length;
  const count2 = values[0].length;
  const result = [];
  for (let index = 0; index < count; index += 1) {
    const result2 = [];
    for (let index2 = 0; index2 < count2; index2 += 1) {
      let total = 0;
      let count3 = 0;
      for (let index3 = index - 1; index3 < index + 2; index3 += 1) {
        for (let index4 = index2 - 1; index4 < index2 + 2; index4 += 1) {
          if (index3 >= 0 && index3 < count && index4 >= 0 && index4 < count2) {
            total += values[index3][index4];
            count3 += 1;
          }
        }
      }
      result2.push(Math.floor(total / count3));
    }
    result.push(result2);
  }
  return result;
}
