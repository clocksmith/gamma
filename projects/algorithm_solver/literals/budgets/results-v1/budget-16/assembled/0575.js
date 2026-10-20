function solve(values) {
    return Math.min(new Set(values).size, Math.floor(values.length / 2));
  }
