const solve = (values) => (Array.from(values).filter(value => !'aeiou'.includes(value)).join(''));
