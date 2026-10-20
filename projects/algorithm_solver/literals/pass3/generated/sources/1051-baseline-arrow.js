const solve = (values) => {
    const sorted = [...values].sort((first, second) => first - second);
    return values.reduce((result, value, index) => result + (value !== sorted[index]), 0);
  };
