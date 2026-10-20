const solve = (values) => {
    let result = 0;
    let count = 0;
    for (const value of values) {
      if (!count) result = value;
      count += value === result ? 1 : -1;
    }
    return result;
  };
