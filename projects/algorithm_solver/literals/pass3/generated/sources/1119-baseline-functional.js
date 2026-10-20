function solve(values) {
    return Array.from(values).filter(value => !'aeiou'.includes(value)).join('');
  }
