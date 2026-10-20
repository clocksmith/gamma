const solve = (values, count) => {
    let previous = 0;
    for (let index = 0; count > 0 && index < values.length; index++) {
      if (values[index] === 0 && previous === 0 && (values[index + 1] ?? 0) === 0) {
        count--;
        previous = 1;
      } else previous = values[index];
    }
    return count <= 0;
  };
