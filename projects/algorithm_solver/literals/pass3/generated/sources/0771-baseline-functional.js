function solve(values, other) {
    const counts = new Set(values);
    return Array.from(other).reduce((result, value) => result + counts.has(value), 0);
  }
