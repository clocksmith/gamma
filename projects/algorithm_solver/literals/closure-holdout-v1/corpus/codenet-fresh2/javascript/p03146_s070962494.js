const input = require('fs').readFileSync('/dev/stdin', 'utf8');

const s = Number(input);

const f = (n) => {
  if (n % 2 === 0) {
    return n / 2;
  } else {
    return 3 * n + 1;
  }
};

const a = (n) => {
  return f(n-1);
};

const list = [];

const listIncludes = (arr, n) => {
  return arr.indexOf(n) >=0 ? true : false;
};

for (var i = s; i < 1000000; i = f(i)) {
  if (listIncludes(list, i)) {
    console.log(list.length + 1);
    break;
  } else {
    list.push(i);
  }
};

