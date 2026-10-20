const solve = (values, other) => {
    const counts = new Set(values);
    let result = 0;
    for (const value of other) {
      if (counts.has(value)) result++;
    }
    return result;
  };
