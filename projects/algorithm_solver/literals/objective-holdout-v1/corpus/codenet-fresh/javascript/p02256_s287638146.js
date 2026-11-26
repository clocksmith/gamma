//config = {input: 'tmp', newline: '\r\n'}; // win
config = {input: '/dev/stdin', newline: '\n'}; //linux

line = require('fs').readFileSync(config.input, 'ascii')
  .split(' ')
  .map(Number);

function gcd(x, y) {
  if (y > x) gcd(y, x);
  if (y % x === 0) return x;
  return gcd(y, x % y);
}

console.log(gcd(line[0], line[1]));