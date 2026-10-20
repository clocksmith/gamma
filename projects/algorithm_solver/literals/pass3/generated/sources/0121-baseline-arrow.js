const solve = (values) => {
    let minimum = Infinity;
    let result = 0;
    for (const value of values) {
      minimum = Math.min(minimum, value);
      result = Math.max(result, value - minimum);
    }
    return result;
  };
