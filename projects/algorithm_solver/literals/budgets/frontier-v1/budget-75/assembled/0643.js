function solve(values, length) {
    let count = values.slice(0, length).reduce((result, value) => result + value, 0);
    let result = count;
    for (let index = length; index < values.length; index++) {
      count += values[index] - values[index - length];
      result = Math.max(result, count);
    }
    return result / length;
  }
