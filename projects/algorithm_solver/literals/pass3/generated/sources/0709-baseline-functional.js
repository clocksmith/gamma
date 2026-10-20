function solve(values) {
    return Array.from(values).map(value => value >= 'A' && value <= 'Z' ? value.toLowerCase() : value).join('');
  }
