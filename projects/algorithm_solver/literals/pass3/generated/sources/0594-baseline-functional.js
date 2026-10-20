function solve(values) {
    const counts = Array.from(values).reduce((counts, value) => counts.set(value, (counts.get(value) || 0) + 1), new Map());
    let result = 0;
    for (const [value, count] of counts) {
      if (counts.has(value + 1)) result = Math.max(result, count + counts.get(value + 1));
    }
    return result;
  }
