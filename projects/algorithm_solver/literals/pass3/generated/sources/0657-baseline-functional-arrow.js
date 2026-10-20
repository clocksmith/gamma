const solve = (values) => {
    const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
    return (counts.get('U') || 0) === (counts.get('D') || 0)
      && (counts.get('L') || 0) === (counts.get('R') || 0);
  };
