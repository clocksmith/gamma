const solve = (values, other) => {
    const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
    for (const value of other) {
      counts.set(value, (counts.get(value) || 0) - 1);
    }
    return [...counts.values()].every(value => value === 0);
  };
