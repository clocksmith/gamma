function solve(values, value) {
    let left = 0;
    let right = values.length;
    while (left < right) {
      const index = Math.floor((left + right) / 2);
      if (values[index] < value) left = index + 1;
      else right = index;
    }
    return values[left] === value ? left : -1;
  }
