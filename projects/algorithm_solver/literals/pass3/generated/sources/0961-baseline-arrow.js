const solve = (values) => {
    const counts = new Set();
    for (const value of values) {
      if (counts.has(value)) return value;
      counts.add(value);
    }
    return null;
  };
